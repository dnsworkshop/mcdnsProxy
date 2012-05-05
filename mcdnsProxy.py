#! env python
"""
  mcdnsProxy - Multicast DNS Proxy

  Repository: https://github.com/dnsworkshop/mcdnsProxy

  Description: A proxy recieving DNS queries over IPv6-UDP Multicast
               and forwarding the query to a defined IPv6 unicast address

  License: Copyright (c) 2012, Carsten Strotmann <carsten@strotmann.de>
           Permission to use, copy, modify, and/or distribute this software for any 
           purpose with or without fee is hereby granted, provided that the above 
           copyright notice and this permission notice appear in all copies.

           THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH 
           REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND 
           FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, 
           OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, 
           DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS 
           ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

  Comment: mcdnsProxy is "proof-of-concept" software. It is not tested or intended for
           production networks. Use at own risk.
  Contact: Carsten Strotmann <carsten@strotmann.de>
"""
import sys
import struct
import socket
import signal
import getopt
import dns
import dns.message
from threading import Thread

class Proxy(Thread):
    """ used to proxy single udp connection 
    """
    BUFFER_SIZE = 4096 
    def __init__(self, listening_address, forward_address):
        print "Server started on", listening_address
        Thread.__init__(self)
        self.bind = listening_address
        self.target = forward_address

    def run(self):

        target = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        target.connect(self.target)

        # listen for incoming connections:
        mcs = socket.inet_pton(socket.AF_INET6, self.bind[0])
        maddr = socket.getaddrinfo(self.bind[0], self.bind[1], socket.AF_INET6, socket.SOCK_DGRAM)[0][-1]
        s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        try:
            s.bind(('',self.bind[1]))
        except socket.error, err:
            print "Couldn't bind server on %r" % (self.bind, )
            print err
            raise SystemExit

        s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, socket.inet_pton(socket.AF_INET6, self.bind[0])+'\0'*4)
        while 1:
            (datagram,addr) = s.recvfrom(self.BUFFER_SIZE)

            if not datagram:
                break
            message = dns.message.from_wire(datagram)
            print "Query:", message.id, message.question
            length = len(datagram)
            sent = target.send(datagram)
            if length != sent:
                print 'cannot send to %r, %r !+ %r' % (self.target, length, sent)
            
            datagram = target.recv(self.BUFFER_SIZE)
            if not datagram:
                break
            message = dns.message.from_wire(datagram)
            print "Answer:", message.id, message.answer
            length = len(datagram)
            sent = s.sendto(datagram,addr)
            if length != sent:
                print 'cannot send to %r, %r !+ %r' % (self.s, length, sent)
        s.close()

def signal_handler(signal, frame):
        print 'Shutting down ...'
        sys.exit(0)

def usage():
    print "mcdnsProxy [-h] [-l IPv6-addr |--listen IPv6-addr] [-f IPv6-addr|--forward IPv6-addr] [-p port| --port port]"
 

def main(argv):
    print "Multicast DNS Proxy for IPv6"
    print "(c) 2012 C. Strotmannn"
    print "https://github.com/dnsworkshop/mcdnsProxy"
    print 

    # ff0x::114 = any private experiment multicast
    # see http://www.iana.org/assignments/ipv6-multicast-addresses/ipv6-multicast-addresses.xml
    listen = "ff02::114"
    forward = "::1"
    port = "53"

    try:                                
        opts, args = getopt.getopt(argv, "hl:f:p:", ["help", "listen=", "forward=", "port="]) 
    except getopt.GetoptError:           
        usage()                          
        sys.exit(2)                     
    for opt, arg in opts:                
        if opt in ("-h", "--help"):      
            usage()                     
            sys.exit()                  
        elif opt in ("-l", "--listen"):                
            listen = arg
        elif opt in ("-f", "--forward"):                
            forward = arg
        elif opt in ("-p", "--port"):                
            port = arg

    LISTENS = (listen,  int(port))
    FORWARDS = (forward, 53)

    while 1:
        proxy = Proxy(LISTENS, FORWARDS)
        proxy.start()
        try:
            proxy.join()
        except:
            print "Quit"
            sys.exit(2)
        print ' [restarting] '

if __name__ == "__main__":
    main(sys.argv[1:])
