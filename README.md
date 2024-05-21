# Eksamen
* To run the applecation, first start the server with  "python applecation.py -s -i 127.0.0.1 -p 8888 -d 8".
* To complete running , run the client with  "python applecation.py -c -i 127.0.0.1 -p 8888 -f Photo.jpg -w 3".
* window size changes. somtimes it is 3,5 and 10.
* Window size (-w) is just in client, does not work in server.
* Destimal is just in server, does not work in client.
* When I use the different window size, the throuput changes.
* I have tested the code in the Mininit. First downloaded the mininet and update with to commando "sudo apt-get update", "sudo apt-get install mininet"
* Then install openvswitch og starte det with "sudo apt install openvswitch-switch", "sudo service openvswitch-switch start"
* Then "sudo python3 simple-topo.py", it should mininet works.
* For test the code in mininet, I use xterm h1 h2. h2 are the server and h1 are the client. then I use "python3 -s -i 10.0.1.2 -p 8888" 
and in h1 I use "python3 -c -i 10.0.1.2 -p 8888 -f Photo.jpg -w 3". the windows size changes from 3 to 5 to 10.
* the throuput with the window size 3 is 0.03Mbps, the throuput with the window size 5 is 0.05Mbps and the throuput with the window size 10 is 0.09Mbps. 
* Then modify the RTT to 50ms and 200ms, and run the code in mininet with diffrent window size (3, 5, and 10).
* Then use discard (-d) on the sirver side and in the client the window size is 20. the throuput is 0.17 Mbps.
* Demonstrate effective code, use tc-netem. I use xterm h1, then ping 10.0.1.2.
