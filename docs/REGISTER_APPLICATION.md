## I: Register a Ford Developer Account


## II: Register an (OAuth) Application with Ford
1. Make sure you are logged in to your ford developer account – if you don't have one, you can register one for free (MFA required)
2. Open https://developer.ford.com/developer-eu<br/>
    <table><tr><td><img src="img001.png" width="375" /></td></tr></table><br/>
    3. Check the box '_I am making a data request under Data Act,..._'  (if this is valid for you) and press the _Continue_ button<br/>
    <table><tr><td><img src="img002.png" width="375" /></td></tr></table><br/>
    4. Check the box '_Yes - This app is for personal use_'
5. Specify any _application name_, any _description_ and any _purpose_
6. Check all the different vehicle types
7. Specify the following URL as the redirect URL in the _Authorization Code_ (purple-marked box):
   - `https://my.home-assistant.io/redirect/oauth`

   <br/>_If you like you can add also additional URLs, but have in mind, they must be either `localhost` or reachable from the public internet (specify a local IP like `http://192.168.1.100` will cause an error message in step 9)._

   <br/>When you e.g., want to use additioallly the URL `http://localhost:8123/auth/external/callback`, then use `https://my.home-assistant.io/redirect/oauth, http://localhost:8123/auth/external/callback` as input.

   <br/>When your HA instance is reachable via the public internet, then __do not it its external URL here, you must always include my.home-assistant.io__. Please be so kind and [read the additional information from the main readme.md](../README.md#user-content-additional-information-about-application-registration-at-ford-and-your-local-ha-instance)<br/><br/>

8. Press _Continue_<br/>
    <table><tr><td><img src="img003.png" width="375" /></td></tr></table><br/>
    9. Check the _All Available Data Categories_, check that _you are not a robot_ (don't cheat) and press _Submit_<br/>
    <table><tr><td><img src="img004.png" width="375" /></td></tr></table>
10. Finally, you have your _Client ID_ and _Client Secret_, save them at a secure place. We will need them shortly. _If this dialog does not appear, then the check if the specified URL is failing. Please double-check that the URL that you might have specified additionally to `https://my.home-assistant.io/redirect/oauth` is reachable from the Ford backend system._

    ### Continue with the configuration
    The first thing you will be requested to do is to configure the application credentials in Home Assistant for the integration. Once this is done, your credentials will be stored by HA and can be used by the integration at any time.

    <table><tr><td><img src="img005.png" width="375" /></td></tr></table><br/>
    Specify any name for the credentials, and then pase your clientId and clientSecret that you have received from the Ford developer portal for your registered application.

    Once the credentials are stored, you will be instantly redirected to the Ford login page in a second browser window, where you should log in with your Ford account.<br/>
    <table><tr><td><img src="img006a.png" width="375" /></td></tr></table>

    If the login is successful, you should see a screen like this one:<br/>
    <table><tr><td><img src="img006b.png" width="375" /></td></tr></table>

    Select the radio button and scroll down to the _Consent_ Button and press it...

    If you have __multiple vehicles__ registered with your Ford account, then in this screen you can select the vehicle you want to connect to HA (by selecting the wanted vehicle's radio button).<br/>
    <table><tr><td><img src="img006c.png" width="375" /></td></tr></table>

    #### When you receive the following error message after pressing the _Consent_ button... 
    <table><tr><td><img src="img007.png" width="375" /></td></tr></table><br/>
    This means, then the global deployment of your registered application did not complete yet (when you created it in the Ford developer portal, there was a message that this might take up to 2h to complete – so please be patient). And try the configuration of the FordConnect Query Integration in HA later.

    #### When your app is successfully configured &amp; registered with Ford, then...
    your browser session will be redirected to the https://my.home-assistant.io website and going to display a screen like this one here:<br/>
    <table><tr><td><img src="img008.png" width="375" /></td></tr></table><br/>
    You should check if the currently configured HA Instance URL is the one you are currently using (is the URL from which you initially started the configuration of the vehicle). Again look at the area marked with the purple box (here in this example I am running my test/integration HA on `http://localhost:8123`).
