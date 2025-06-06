#!/usr/bin/env python3

# Web server
from flask import Flask
from flask import request
from flask import send_file
from flask import redirect
from flask import make_response
import logging

# Threaded
from multiprocessing import Process
import asyncio
import signal

# File access
import argparse
import os
from os import listdir
from os.path import isfile, join
import mimetypes

# Data formatting
import json

# Setup argument for path
parser = argparse.ArgumentParser(
                    prog='Live Image Gallery',
                    description='Provides web interface for viewing live updating folder of photos.',
                    epilog='Provide path to folder to host')
parser.add_argument('path')           # positional argument
args = parser.parse_args()


class WebServer(object):

    def __init__(self):

        self.app = Flask("Flask web server")

        # Uncomment to reduce access logging
        #self.app.logger.disabled = True
        #log = logging.getLogger('werkzeug')
        #log.disabled = True

        # Setup flask routes
        self.app.add_url_rule('/','home', self.gallery)
        self.app.add_url_rule('/img/<name>','img', self.img)
        self.app.add_url_rule('/files.json','files', self.files)

    async def start(self):
        """ Run Flask in a process thread that is non-blocking """
        print("Starting Flask")
        self.web_thread = Process(target=self.app.run, kwargs={"host":"0.0.0.0","port":5001})
        self.web_thread.start()

    def stop(self):
        """ Send SIGKILL and join thread to end Flask server """
        self.web_thread.terminate()
        self.web_thread.join()


    def gallery(self):
        """ Main view page generation """
        output = """
<img style="display:block; width:100%" id='main-view'/>
<div id='latest'>Latest</div>
<ul id='file-list'>
</ul>

<ul id='dir-list'>
</ul>
        <script>
/* I'm not a JS dev: https://stackoverflow.com/a/5448595 */
function findGetParameter(parameterName) {
    var result = null,
        tmp = [];
    location.search
        .substr(1)
        .split("&")
        .forEach(function (item) {
          tmp = item.split("=");
          if (tmp[0] === parameterName) result = decodeURIComponent(tmp[1]);
        });
    return result;
}


img_id = "latest"
img_data = ""

function json_read(data)
{
    subdir=findGetParameter("subdir");

    param="";
    if(subdir == null)
    {
    subdir="";
    }else{

    param="?subdir="+subdir;
}
    img_data = data
    if(img_data.length ==0)
    {
      main.src = "";
      chat_list.textContent = '';
      return
    }
    late_button = document.getElementById("latest");
    late_button.addEventListener('click', function(e) {
            set_image("latest");
        });

    temp = document.createElement("ul");
    temp.id = "file-list";
    i=0;
    img_data['all'].slice(0,25).forEach((c) => {
        li = document.createElement("li");
        img = document.createElement("img");
        img.src = "/img/"+c['path']+param;
        img.addEventListener('click', function(e) {
            set_image("/img/"+c['path']);
        });

        li.appendChild(img);

        temp.appendChild(li);

        i+=1;
    });
    chat_list = document.getElementById("file-list");
    chat_list.replaceWith(temp);


    dir_list = document.getElementById("dir-list");
    dir_list.textContent = '';

    li = document.createElement("li");
    a = document.createElement("a");
    a.textContent = "Home";
    a.href = "/";

    li.appendChild(a);
    dir_list.appendChild(li);


    i=0;
    img_data['dirs'].forEach((c) => {
        li = document.createElement("li");
        a = document.createElement("a");
        a.textContent = subdir+c;
        a.href = "?subdir="+subdir+c;

        li.appendChild(a);
        dir_list.appendChild(li);

        i+=1;
    });



    if (img_id == "latest")
    {
        set_image("latest");
    }
}

function set_image(img)
{
    subdir=findGetParameter("subdir");

    param="";
    if(subdir == null)
    {
    subdir="";
    }else{

    param="?subdir="+subdir;
}

    img_id = img;
    if (img == "latest")
    {
        path = "/img/"+img_data['latest']['path']+param;
    }else{
        path = img;
    }

    main = document.getElementById("main-view");
    main.src = path;
}

function data_fetch()
{
  subdir=findGetParameter("subdir");

  param=""
  if(subdir != null)
  {
    param="?subdir="+subdir
  }


  fetch('files.json'+param)
    .then((response) => response.json())
    .then((data) => json_read(data));

  setTimeout(data_fetch,1000)
}
setTimeout(data_fetch,1000)

    </script>
    <style>
    body{
    background-color: #000;
    margin: 0px;
    padding: 0px;
    }

    #latest
    {
        text-align: center;
  vertical-align: middle;
        background-color: #333;
        width: 100%;
        font-size: 3em;
        font-family: sans-serif;
    }

    #file-list li{
        display: inline-block;
        width: 20%;
    }
    #file-list img{
        display: block;
        width: 100%;
    }
    #file-list img{
        display: block;
        width: 100%;
    }
    #file-list
    {
    margin: 0px;
    padding: 0px;
    }
    #dir-list
    {
    margin: 0px;
    padding: 0px;
    }
    #dir-list li
    {
    list-style:none;
    margin: 0px;
    padding: 0px;
    border-bottom: 1px solid #333;
    }
    </style>
"""
        return output

    def files(self):
        """ JSON list of files in path with latest file access """
        subdir=request.args.get('subdir')
        if subdir is None:
            subdir = ""

        # Clear old list
        gallery_files = {}
        gallery_files["all"] = []

        # Get files
        onlyfiles = [f for f in listdir(args.path+"/"+subdir) if isfile(join(args.path+"/"+subdir, f))]
        gallery_files["dirs"]  = [ f.path.replace(args.path+"/"+subdir,"") for f in os.scandir(args.path+"/"+subdir) if f.is_dir() ]

        # Format data
        for filepath in onlyfiles:
            mime = mimetypes.guess_type(args.path+"/"+subdir+"/"+filepath)

            if mime[0].startswith("image"):
                gallery_files["all"].append({"path":filepath,"time" : os.path.getmtime(args.path+"/"+subdir+"/"+filepath)} )

        # Sort by modification time
        gallery_files["all"] = sorted(gallery_files["all"], key=lambda d: d['time'])

        # Get latest file
        gallery_files["latest"] = gallery_files["all"][0]

        # Return JSON
        return json.dumps(gallery_files)

    def img(self,name=None):
        """ Send image file from path to client """
        subdir=request.args.get('subdir')
        if subdir is None:
            subdir = ""

        return send_file(f"{args.path}//{subdir}//{name}")

# Create servev
http = WebServer()
http.gallery_files = []

# State value for exit
global loop_state
loop_state = True

async def main_loop():
    """ Blocking main loop to provide time for async tasks to run"""
    global loop_state
    while loop_state:
        await asyncio.sleep(1)


async def main():
    """ Start connections to async modules """

    # Setup CTRL-C signal to end programm
    signal.signal(signal.SIGINT, exit_handler)
    print('Press Ctrl+C to exit program')

    # Start async modules
    L = await asyncio.gather(
        http.start(),
        main_loop()
    )


def exit_handler(sig, frame):
    """ Handle CTRL-C to gracefully end program and API connections """
    global loop_state
    print('You pressed Ctrl+C!')
    loop_state = False

# Start web server
asyncio.run(main())
# Run after CTRL-C
http.stop()
