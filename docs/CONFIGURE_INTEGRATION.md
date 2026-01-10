## Configure the Integration

### Requirements
- A Ford Developer Account
- [A registered _Ford Application_ with the required permissions](REGISTER_APPLICATION.md) 
- The clientId and clientSecret for this application
- Have installed the integration via HACS (or manual copy of the files)

#### Here is an example of the required app credentials:
```
{
  "clientId":"1da26426-c447-48a4-afc6-6afe28f06aa1",
  "secret":"HMF8Q~.WIno6FFy6rwe3X~7GVcHaD8YjBemwRcvH"
}
```
___These are just example credentials – and they will not work – don't waste your time by trying to use them!___

### In Home Assistant
[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=fordconnect_query)

or
1. Go to  `Settings` -> `Devices & Services` area
2. Add the new integration `FordConnect Query (for EU)`

### Continue with the configuration
The first thing you will be requested to do is to configure the application credentials in Home Assistant for the integration. Once this is done, your credentials will be stored by HA and can be used by the integration at any time.

![img005.png](img005.png)<br/>
Specify any name for the credentials, and then pase your clientId and clientSecret that you have received from the Ford developer portal for your registered application.

Once the credentials are stored, you will be instantly redirected to the Ford login page in a second browser window, where you should log in with your Ford account.<br/>
![img006a.png](img006a.png)

If the login is successful, you should see a screen like this one:<br/>
![img006b.png](img006b.png)

Select the radio button and scroll down to the _Consent_ Button and press it...

If you have __multiple vehicles__ registered with your Ford account, then in this screen you can select the vehicle you want to connect to HA (by selecting the wanted vehicle's radio button).<br/>
![img006c.png](img006c.png)

#### When you receive the following error message after pressing the _Consent_ button... 
![img007.png](img007.png)<br/>
This means, then the global deployment of your registered application did not complete yet (when you created it in the Ford developer portal, there was a message that this might take up to 2h to complete – so please be patient). And try the configur the FordConnect Query Integraton in HA later.

#### When your app is successfully configured &amp; registered with Ford, then...
The your browser session will be redirected to the https://my.home-assistant.io website and going to display a screen like this one here:<br/>
![img008.png](img008.png)<br/>
You should check if the currently configured HA Instance URL is the one you are currently using (is the URL from which you initially started the configuration of the vehicle). Again look at the area marked with the purple box (here in this example I am running my test/integration HA on `http://localhost:8123`).

If this URL is not correct, then press the _pencil_ icon and specify the correct URL.

Complete this step by pressing the blue _Link account_ button.

Now you will return to your HA instance, and the integration now can use the authorisation `code` in order to request the final access token to access the vehcile data for your car.

When the process does not complete on your home assistant instance, then please [enable the debug log of the integration as documented here](https://github.com/marq24/ha-fordconnect-query?tab=readme-ov-file#want-to-report-an-issue) and start with configuration of the integration again, after you have restarted your HA instance. Now the integration will log each step of the process, and when you going to create an [issue](https://github.com/marq24/ha-fordconnect-query/issues), then you can attach the log file (or send it to me via email). TIA