## Configure the Integration

### Requirements
- A Ford Developer Account
- [A registered Ford Application with the required permissions](REGISTER_APPLICATION.md) 
- The clientId and clientSecret for this application
- Have installed the integration via HACS (or manual copy of the files)

#### Here is again an example for the required app credentials:
```
{
  "clientId":"1da26426-c447-48a4-afc6-6afe28f06aa1",
  "secret":"HMF8Q~.WIno6FFy6rwe3X~7GVcHaD8YjBemwRcvH"
}
```
__This one does not work!__

### In Home Assistant
[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=fordconnect_query)

or
1. Go to  `Settings` -> `Devices & Services` area
2. Add the new integration `FordConnect Query (for EU)`

### Continue with the configuration
![img005.png](img005.png)<br/>
Specify any name for the credentials, and then pase your clientId and clientSecret that you have received from the Ford developer portal for your registered application.

Once the credentials are stored, you will be instantly redirected to the Ford login page in a second browser window, where you should log in with your Ford account.

If the login is successful, you should see a screen like this one:<br/>
![img006.png](img006.png)

Select the radio button and scroll down to the _Consent_ Button and press it...

#### When you receive the following error message after pressing the consent button... 
![img007.png](img007.png)<br/>
This means, then the global deployment of your registered application did not complete yet (when you created it in the Ford developer portal, there was a message that this might take up to 2h to complete – so please be patient). And try the configur the FordConnect Query Integraton in HA later.

#### When your app is successfully configured &amp; registered with Ford, then...
The following screen will appear<br/>
![img008.png](img008.png)<br/>
You should check if the currently configured HA Instance URL is the one you are currently using – again look at the area marked with the purple box (here in this example I am running my test/integration HA on `http://localhost:8123`).

If this URL is not correct, then press the _pencil_ icon and specify the correct URL.

Complete this step by pressing the _Link account_ button.

Now you will return to your HA instance, and the integration now can use the `code` in order to request the final access token to access the vehcile data for your car. 