import binascii, urllib, socket, random, struct
from bcode import bdecode
from urlparse import urlparse, urlunsplit
import sys

"""
Original file from https://github.com/erindru/m2t/blob/master/m2t/scraper.py

"""


def scrape(tracker, hashes):
    tracker = tracker.lower()
    parsed = urlparse(tracker)
    if parsed.scheme == "udp":
        return scrape_udp(parsed, hashes)

    if parsed.scheme in ["http", "https"]:
        if "announce" not in tracker:
            raise RuntimeError("%s doesnt support scrape" % tracker)
        parsed = urlparse(tracker.replace("announce", "scrape"))
        return scrape_http(parsed, hashes)

    raise RuntimeError("Unknown tracker scheme: %s" % parsed.scheme)


def scrape_udp(parsed_tracker, hashes):
    print "Scraping UDP: %s for %s hashes" % (parsed_tracker.geturl(), len(hashes))
    if len(hashes) > 74:
        raise RuntimeError("Only 74 hashes can be scraped on a UDP tracker due to UDP limitations")
    transaction_id = "\x00\x00\x04\x12\x27\x10\x19\x70";
    connection_id = "\x00\x00\x04\x17\x27\x10\x19\x80";
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(8)
    conn = (socket.gethostbyname(parsed_tracker.hostname), parsed_tracker.port)

    # Get connection ID
    req, transaction_id = udp_create_connection_request()
    sock.sendto(req, conn);
    buf = sock.recvfrom(2048)[0]
    connection_id = udp_parse_connection_response(buf, transaction_id)

    # Scrape away
    req, transaction_id = udp_create_scrape_request(connection_id, hashes)
    sock.sendto(req, conn)
    buf = sock.recvfrom(2048)[0]
    return udp_parse_scrape_response(buf, transaction_id, hashes)


def scrape_http(parsed_tracker, hashes):
    print "Scraping HTTP: %s for %s hashes" % (parsed_tracker.geturl(), len(hashes))
    qs = []
    for hash in hashes:
        url_param = binascii.a2b_hex(hash)
        qs.append(("info_hash", url_param))
    qs = urllib.urlencode(qs)
    pt = parsed_tracker
    url = urlunsplit((pt.scheme, pt.netloc, pt.path, qs, pt.fragment))
    handle = urllib.urlopen(url);
    if handle.getcode() is not 200:
        raise RuntimeError("%s status code returned" % handle.getcode())
    decoded = bdecode(handle.read())
    ret = {}
    for hash, stats in decoded['files'].iteritems():
        nice_hash = binascii.b2a_hex(hash)
        s = stats["downloaded"]
        p = stats["incomplete"]
        c = stats["complete"]
        ret[nice_hash] = {"seeds": s, "peers": p, "complete": c}
    return ret


def udp_create_connection_request():
    connection_id = 0x41727101980  # default connection id
    action = 0x0  # action (0 = give me a new connection id)
    transaction_id = udp_get_transaction_id()
    buf = struct.pack("!q", connection_id)  # first 8 bytes is connection id
    buf += struct.pack("!i", action)  # next 4 bytes is action
    buf += struct.pack("!i", transaction_id)  # next 4 bytes is transaction id
    return (buf, transaction_id)


def udp_parse_connection_response(buf, sent_transaction_id):
    if len(buf) < 16:
        raise RuntimeError("Wrong response length getting connection id: %s" % len(buf))
    action = struct.unpack_from("!i", buf)[0]  # first 4 bytes is action

    res_transaction_id = struct.unpack_from("!i", buf, 4)[0]  # next 4 bytes is transaction id
    if res_transaction_id != sent_transaction_id:
        raise RuntimeError("Transaction ID doesnt match in connection response! Expected %s, got %s"
                           % (sent_transaction_id, res_transaction_id))

    if action == 0x0:
        connection_id = struct.unpack_from("!q", buf, 8)[0]  # unpack 8 bytes from byte 8, should be the connection_id
        return connection_id
    elif action == 0x3:
        error = struct.unpack_from("!s", buf, 8)
        raise RuntimeError("Error while trying to get a connection response: %s" % error)
    pass


def udp_create_scrape_request(connection_id, hashes):
    action = 0x2  # action (2 = scrape)
    transaction_id = udp_get_transaction_id()
    buf = struct.pack("!q", connection_id)  # first 8 bytes is connection id
    buf += struct.pack("!i", action)  # next 4 bytes is action
    buf += struct.pack("!i", transaction_id)  # followed by 4 byte transaction id
    # from here on, there is a list of info_hashes. They are packed as char[]
    for hash in hashes:
        hex_repr = binascii.a2b_hex(hash)
        buf += struct.pack("!20s", hex_repr)
    return (buf, transaction_id)


def udp_parse_scrape_response(buf, sent_transaction_id, hashes):
    if len(buf) < 16:
        raise RuntimeError("Wrong response length while scraping: %s" % len(buf))
    action = struct.unpack_from("!i", buf)[0]  # first 4 bytes is action
    res_transaction_id = struct.unpack_from("!i", buf, 4)[0]  # next 4 bytes is transaction id
    if res_transaction_id != sent_transaction_id:
        raise RuntimeError("Transaction ID doesnt match in scrape response! Expected %s, got %s"
                           % (sent_transaction_id, res_transaction_id))
    if action == 0x2:
        ret = {}
        offset = 8;  # next 4 bytes after action is transaction_id, so data doesnt start till byte 8
        for hash in hashes:
            seeds = struct.unpack_from("!i", buf, offset)[0]
            offset += 4
            complete = struct.unpack_from("!i", buf, offset)[0]
            offset += 4
            leeches = struct.unpack_from("!i", buf, offset)[0]
            offset += 4
            ret[hash] = {"seeds": seeds, "peers": leeches, "complete": complete}
        return ret
    elif action == 0x3:
        # an error occured, try and extract the error string
        error = struct.unpack_from("!s", buf, 8)
        raise RuntimeError("Error while scraping: %s" % error)


def udp_get_transaction_id():
    return int(random.randrange(0, 255))


def get_leech_seed_data(uri_list, hash_list):
    result = {}
    for uri in uri_list:
        try:
            scrape_data = scrape(uri, hash_list)
            is_error = False
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print "Error: ", uri
            is_error = True
        for t_hash in hash_list:
            if t_hash not in result:
                result[t_hash] = {'peers': 0, 'seed': 0}
            if not is_error:
                result[t_hash]['peers'] += scrape_data[t_hash]['peers']
                result[t_hash]['seed'] += scrape_data[t_hash]['seeds']
    return result


if __name__ == "__main__":
    t_hashs = ["EEF64FCAA6C6222D0E0D67E100BB68D83E4309D2", "74ADB0BA0D8DFDBA175C2991CF8AD0915C4DFC02"]
    t_scarpe = ["udp://open.demonii.com:1337/announce",
                "udp://tracker.openbittorrent.com:80/announce",
                "udp://tracker.publicbt.com:80/announce",
                "udp://tracker.istole.it:80/announce"]
    print get_leech_seed_data(t_scarpe, t_hashs)
