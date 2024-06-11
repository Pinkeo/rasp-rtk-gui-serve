# receiving GNSS Location data via Sparkfun GNSS Recjoning from Raspberrypi to AWS EC2 server via WebSocket

#### This have 2 section if you don't want to use AWS Cloud you can use something like Ngrok to access the website from outside local network

## Using local host and Ngrok
1. Clone this repository to your Raspberry pi
   ```
   git clone https://github.com/Pinkeo/rasp-rtk-gui-serve.git 
   ```
2. create virtual environment
   install venv
   ```
   pip install python3.12-venv
   ```
   then
   ```
   python3 -m venv venv
   ```
   activate it
   ```
   source venv/bin/activate
   ```
4. cd to your the repository directory and install requirements.txt
   ```
   pip install requirements.txt
   ```
   | NOTE: if your raspberrypi doesn't have Sparkfun libraries you should install requirementss.txt
5. run webserver
   ```
   python3 app.py
   ```
   if the app run correctly you can access via http://localhost:5000
6. run client file
   open another shell and cd to your directory and activate virtual environment then run
   ```
   python3 geo_coords_dead_reckoning_CLIENT.py
   ```
if everything installed correctly you can see it running and see the update in the webpage

### connect to Ngrok 
you must have ngrok account go to https://ngrok.com/ to create one.
Than install it in your Raspberry Pi (you can read the docomentation in theire website).
after installed, run this command
```
ngrok http 5000
```
then you can go to the url that ngrok genered for you
| the important thing to note here is: when you go to ngrok url it encrypts the connection to https if in that why you should make some change in the script inside the index.html (this one `var socket = io.connect('http://' + document.domain + ':' + location.port + '/');` ), change `http` to `wss` then you're good to go.  


## Using AWS EC2 
1. create EC2 instance with Ubuntu and connect
2. update apt
   ```
   sudo apt update
   sudo apt upgrate
   ```
3. clone this repository
   ```
   git clone https://github.com/Pinkeo/rasp-rtk-gui-serve.git 
   ```
   cd to the directory and install venv
   ```
   pip install python3.12-venv
   ```
   then
   ```
   python3 -m venv venv
   ```
   activate it
   ```
   source venv/bin/activate
   ```
4. cd to your the repository directory and install requirements.txt
   ```
   pip install requirements.txt
   ```
5. install gunicorn, eventlet and nginx
   ```
   pip install gunicorn
   pip install -U eventlet
   sudo apt install nginx
   ```
6. make a little bit change in your app.py
   ```
   sudo nano app.py
   ```
   and add this to the first line of the code
   ```
   import eventlet
   eventlet.monkey_patch()
   ```
   modify the last line of code
   ```
   socketio.run(app, debug=True, host='0.0.0.0', port=5000,cors_allowed_origins='*',async_mode='eventlet')
   ```
7. edit gunicorn unit file
   ```
   sudo nano /etc/systemd/system/rtk-gui.service
   ```
   add this
   ```
   [Unit]
    Description=Gunicorn instance for a simple rtk-gui app
    After=network.target
   [Service]
    User=ubuntu
    Group=www-data
    WorkingDirectory=/home/ubuntu/rasp-rtk-gui-serve
    ExecStart=/home/ubuntu/rasp-rtk-gui-serve/venv/bin/gunicorn -b localhost:5000 app:app
    Restart=always
   [Install]
    WantedBy=multi-user.target
   ```
   save and run this
   ```
   sudo systemctl daemon-reload
   sudo systemctl start rtk-gui
   sudo systemctl enable rtk-gui
   ```
8. edit nginx config
   ```
   sudo nano /etc/nginx/sites-available/rtk-gui
   ```
   add this
   ```
    server {
    listen 80;
    listen [::]:80;
    server_name your_EC2_public_IP;
    location / {
         include proxy_params;
         proxy_pass http://localhost:5000;
        }
    location /socket.io {
         proxy_pass http://localhost:5000/socket.io;
         proxy_redirect off;
         proxy_buffering off;
         proxy_set_header Host $host;
         proxy_set_header X-Real-IP $remote_addr;
         proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
         proxy_http_version 1.1;
         proxy_set_header Upgrade $http_upgrade;
         proxy_set_header Connection “Upgrade”;
         proxy_hide_header Access-Control-Allow-Origin;
        }
    }  
   ```
    then run this command
    ```
    sudo systemctl start rtk-gui
    sudo systemctl enable rtk-gui
    ```
9. restart the service
   ```
       sudo systemctl restart rtk-gui
       sudo systemctl restart rtk-gui.service
       sudo systemctl restart nginx
   ```
   and here you go!!!!!
   if it not working youcan check by these 3 commands
   ```
      sudo systemctl status rtk-gui
      sudo systemctl status rtk-gui.service
      sudo systemctl status nginx
   ```
   if you want to see in detail
   ```
      sudo journalctl -u rtk-gui.service
   ```
10. change the endpoint in client sript `geo_coords_dead_reckoning_CLIENT.py` instead of `localhost:5000` you should add your EC2 public IP with `/socket.io`
    ```
    async def send_location():
    await sio.connect('http://your_ec2_public_IP/socket.io')
    ```
  
