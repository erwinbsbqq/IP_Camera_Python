1.modify mac address

2.update apt-get, command as: 
  sudo apt-get update;sudo apt-get 

3.install cloudq sdk and bind board, command as: 
  sudo apt-get install python-dev python-pip;sudo pip install simplejson;sudo apt-get install cloudq

4.install libraries, command as: 
  sudo apt-get install python-imaging python-numpy python-imaging-tk python-opencv 

5.install qrcode library, command as: 
  tar -zxvf qrcode-5.1.tar.gz
  cd qrcode-5.1
  sudo python setup.py install

6.run ip camera; command as: sudo python ip_camera.py

Note: 1.if you had installed Cloudq in Gobian, Step 1~3 can be skipped.
      2.some libraries can also be skiiped if you had installed them.