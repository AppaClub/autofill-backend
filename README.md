**Steps**

**1. Running pdf using pdf-js**
Download pdf-js from this link https://objects.githubusercontent.com/github-production-release-asset-2e65be/1663468/ccbc5560-92c7-4944-a707-b20108b25165?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=releaseassetproduction%2F20241118%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20241118T083755Z&X-Amz-Expires=300&X-Amz-Signature=441cb65983b4203a2d9addbe58e82d710159748a06d129e5beb0f40cb49781a8&X-Amz-SignedHeaders=host&response-content-disposition=attachment%3B%20filename%3Dpdfjs-4.8.69-dist.zip&response-content-type=application%2Foctet-stream

Place your pdf in the "web" folder.
Open terminal from the root folder and type "python -m http.server" to host and goto http://localhost:8000/web/viewer.html to view pdf

**2. Setting up**
Install the extension by clicking load unpacked in manage extensions tab of Chrome and locating the extension folder

Run the backend python code by running flask run --port=5055 --host=0.0.0.0



 
