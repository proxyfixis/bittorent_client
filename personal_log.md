## Issues I ran into : 

The tracker returns only one peer even with a numwants parameter , can't figure out why  : 
    Its the server side policy for ubuntu , will have to check with different torrents

Tracker doesn't always give out the peers in compact byte format - gives in a list format when address is ipv6 : 
    just add an if else block





## Reading : 

DHT and PEX in p2p file sharing
How does UDP fit in ?

## random learning : 

TCP is byte specific , doesnt care about message boundaries - send(hello) and send(World) might be recieved as hell oworld or helloworld or anything else idk
it only cares about the order

to solve this 
the bittorent protocol - sends things only in sets of 68 BYTES - ONLY FOR THE HANDSHAKE

AFTER the handshake - it uses length prefixed - first 4 bytes tell how many bytes follow

