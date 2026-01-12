# FordConnect Query Home Assistant Integration 2026 (EV/PHEV/Petrol/Diesel)
## Supporting all Ford vehicles with FordPass™ connectivity
<!--

## Welcome to the FordConnect Query Integration
This is an alternative [integration to FordPass](https://github.com/marq24/ha-fordpass), making use of the FordConnect Query API. This API provides __read-only__ access to the vehicle data.
### Requirements
- Your car must have the latest on-board modem functionality and have been registered/authorized with the FordPass™ application
- An API credential pair previously registered with the EU Ford developer portal.

Further information can be found in [_the Application Registration Guide_. This includes a step-by-step procedure](https://github.com/marq24/ha-fordconnect-query/blob/main/docs/REGISTER_APPLICATION.md) to register an application at Fords EU developer portal.
### Need further instructions?
All other setup details can be found in the [Integration Setup Guide](https://github.com/marq24/ha-fordconnect-query/blob/main/docs/CONFIGURE_INTEGRATION.md)
### Final note
If you find this integration useful, please consider supporting me as a GitHub project sponsor (or in one of the other ways [described here in my profile@GitHub](https://github.com/marq24)) – thank you to those who already do – you're all amazing!
-->
<!--
## Willkommen zur FordConnect Query Integration
Dies ist eine [alternative Integration zu FordPass](https://github.com/marq24/ha-fordpass), die die FordConnect Query API nutzt. Diese API bietet __read.only__ Zugriff auf Deine Fahrzeugdaten.
### Voraussetzungen
- Dein Fahrzeug muss über die neueste On-Board-Modem-Funktionalität verfügen und bei der FordPass™-Anwendung registriert/autorisiert sein.
- Einen API-Schlüssel, der zuvor im EU-Ford-Entwicklerportal registriert wurde.

Weitere Informationen findest Du [im _Application Registration Guide_. Dort findest Du auch eine Schritt-für-Schritt-Anleitung](https://github.com/marq24/ha-fordconnect-query/blob/main/docs/REGISTER_APPLICATION.md) zur Registrierung eines solchen Schlüssels.
### Benötigst Du weitere Hilfe?
Alle weiteren Einrichtungsdetails findest Du [hier im _Integration Setup Guide_](https://github.com/marq24/ha-fordconnect-query/blob/main/docs/CONFIGURE_INTEGRATION.md).
### Abschließender Hinweis in eigener Sache
Wenn Du diese Integration nützlich findest, dann bitte denk doch bitte darüber nach, ob Du mich nicht vielleicht als GitHub-Projekt-Sponsor (oder auf eine der anderen in [meinem Profil@GitHub](https://github.com/marq24) beschriebenen Art) unerstützen möchtest – vielen Dank an die Menschen, die dies bereits tun – Ihr seid großartig!
-->


<!--
> [!NOTE]  
> Highlights information that users should take into account, even when skimming.

> [!TIP]
> Optional information to help a user be more successful.

> [!IMPORTANT]  
> Crucial information necessary for users to succeed.

> [!WARNING]  
> Critical content demanding immediate user attention due to potential risks.

> [!CAUTION]
> Negative potential consequences of an action.
-->

[![hacs_badge][hacsbadge]][hacs] [![hainstall][hainstallbadge]][hainstall] [![Wero][werobadge]][wero] [![Revolut][revolutbadge]][revolut] [![PayPal][paypalbadge]][paypal] [![github][ghsbadge]][ghs] [![BuyMeCoffee][buymecoffeebadge]][buymecoffee]

> [!WARNING]
> ## General Disclaimer
> **This integration is not officially supported by Ford, and as such, using this integration could have unexpected/unwanted results.**
>
> Please be aware that I am developing this integration to the best of my knowledge and belief, but can't give a guarantee. Therefore, use this integration **at your own risk**! [ _I am not affiliated with Ford in any way._]
>
> ## FordPass™/The Lincoln Way™ Account Disclaimer 
> **The use of this HA integration could lead to a (temporary) lock of your FordPass™/The Lincoln Way™ account.** (this is quite unlikely — since this integration is fully compliant with the required OAuth procedures by Ford) but since Ford does not officially support this integration, using it could result in your being locked out from your account.
>
> **It's recommended** to use/create a **separate FordPass™/The Lincoln Way™ account** for this integration ([see the 'step-by-step' procedure further below](https://github.com/marq24/ha-fordconnect-query?tab=readme-ov-file#use-of-a-separate-fordpassthe-lincoln-way-account-is-recommended)).

---

> [!NOTE]
> This is a __cloud polling integration__, which means that the data is requested from Ford backend systems to Home Assistant via a https connection every 60 seconds. I am working on making this configurable via the HA UI.
> 
> It would be quite gentle if you could consider supporting the development of this integration by any kind of contribution — TIA

---

> [!NOTE]
> My main motivation comes from the fact that I have developed the [FordPass Integration](https://github.com/marq24/ha-fordpass), and it's totally unknown how long this is continued to work.
> 
> YES I am aware that the FordConnect Query Integration has __ONLY READ__ capabilities. But that's IMHO way better to be able to get to the vehicle sensor data (when the FordPass Integration will stop working).
> 
---

> [!IMPORTANT]
> ## OAuth Integration Setup 
> 1. You need to register a Ford developer account to be able to use this integration.
> 2. You need to register a Ford application in the __EU__ developer portal. 
> 3. You need to configure OAuth Application Credentials in HA that can be used by this integration. (will be done automatically via the integration setup)
---

## Sample panel
![
https://raw.githubusercontent.com/marq24/ha-fordconnect-query/refs/heads/main/docs/sample-panel.png](
https://raw.githubusercontent.com/marq24/ha-fordconnect-query/refs/heads/main/docs/sample-panel.png)

## Requirements
1. Your car must have the latest onboard modem functionality and have been registered/authorized with the FordPass™/The Lincoln Way™ application.<br/>
2. You need a Home Assistant instance (v2025.11 or higher) with the [HACS](https://hacs.xyz/docs/use/#getting-started-with-hacs) custom integration installed.<br/>
3. [You __must have registered an application with Ford__](./docs/REGISTER_APPLICATION.md).

> [!IMPORTANT]
> This is a HACS custom integration — not a Home Assistant Add-on. Don't try to add this repository as an add-on in Home Assistant.
> 
> The IMHO simplest way to install this integration is via the two buttons below ('_OPEN HACS REPOSITORY ON MY HA_' and '_ADD INTEGRATION TO MY HA_').

## Installation Instructions

### Step 1. HACS add the Integration

[![Open your Home Assistant instance and adding repository to HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=marq24&repository=ha-fordconnect-query&category=integration)

1. In HA HACS, you need to add a new custom repository (via the 'three dots' menu in the top right corner).
2. Enter `https://github.com/marq24/ha-fordconnect-query` as the _Repository URL_ and select the _Type_ `Integration`.
3. After adding the new repository, you can search for `fordconnect` in the search bar.
4. Install the 'correct' (aka 'this') FordConnect Query integration (v2026.1.0 or higher).
6. Restart HA.

### Step 2. Set up the Integration

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=fordconnect_query)

7. After the restart go to  `Settings` -> `Devices & Services` area
8. Add the new integration `FordConnect Query` and [follow the instructions provided in a seperate document in this repository](./docs/CONFIGURE_INTEGRATION.md).


## Usage with EVCC

[All information, how to use this integration as a provider for Ford EV data can be found in a separate section in this repository.](https://github.com/marq24/ha-fordpass/blob/main/doc/EVCC.md)


## Use of a separate FordPass™/The Lincoln Way™ account is recommended

> [!TIP]
> It's recommended to use a separate FordPass™/The Lincoln Way™ account for this integration. This is to prevent any issues with the FordPass™/The Lincoln Way™ account being locked due to the polling of the API.

Here is a short procedure how to create and connect a second account (for FordPass™):

1. Create a new FordPass™ account (via the regular Ford website) with a different email address (and confirm this account by eMail). All this can be done via a regular web browser.<br/>__It's important that you can access this eMail account from your mobile phone where the FordPass™ App is installed__ (we need this in step 6).
2. On a mobile Device: Open the FordPass™ app (logged in with your original account), then you can select `Settings` from the main screen (at the bottom there are three options: `Connected Services >`, `Location >` & `Settings >`)
3. On the next screen select `Vehicle Access` (from the options: `Phone As A Key >`, `Software updates >` & `Vehicle Access >`)
4. Select `Invite Driver(s) Invite` and then enter the next screen the eMail address of the new account you created in step 1. 
5. Now you can log out with your main account from the FordPass™ app and log-in again with the new account (created in step 1).
6. Wait till the invitation eMail arrives and accept the invitation with the button at the bottom of eMail.<br/>__This step must be performed on the mobile device where the FordPass™ app is installed!__ (since only on a mobile device with installed FordPass™ you can open the acceptance-link of this eMail)
7. Finally, you should now have connected your car to the new FordPass™ account.
8. You can now log out again of the FordPass™ app with your second account and re-login with your original FordPass™ account.
9. You can double-check with a regular browser that the car is now accessible with the new account by web.

If accepting the invitation doesn't work or results in a blank screen in the Ford app, try adding the vehicle by VIN to the new account first, then accepting the invite.

## Multi-Vehicle Support

This integration supports multiple vehicles for in your FordPass™ account.

When you have registered multiple vehicles in your FordPass™ account, then you can add the integration multiple times. Make sure, when you select the vehicle you want to use from the list of available vehicles at the _consent_ page from Ford (details can be found [in the short integration configuration tutorial](./docs/CONFIGURE_INTEGRATION.md)).


<!--
## Services

### Clear Tokens
If you are experiencing any sign-in issues, please try clearing your tokens using the "clear_tokens" service call.

### Poll API (local refresh) — also available as a button in the UI
This service allows you to sync the data of the integration (read via the websocket) with the Ford backends by manually polling all data. This can become Handy if you want to ensure that HA data is in sync with the Ford backend data.

### Request Update (remote refresh) — also available as a button in the UI
This service will contact the modem in the vehicle and request to sync data between the vehicle and the ford backends. **Please note that this will have an impact on the battery of your vehicle.**
-->

> [!Note]
> ### Not every Ford is the same 
> Sounds a bit strange — but the EV Explorer or EV Capri (European models) are based on a platform from Volkswagen. As a consequence, not every sensor will be available for these vehicles, since the Ford backend does not provide the corresponding data for these vehicles [e.g. 12V battery, RC seats, or the target charge level].


## Sensors
**Sensors may change as the integration is being developed**
~~Supports Multiple Regions~~

| Sensor Name                        | Petrol/Diesel | (P)HEV | &nbsp;(B)EV&nbsp; |
|:-----------------------------------|:-------------:|:------:|:-----------------:|
| Odometer                           |       ✔       |   ✔    |         ✔         |                 
| Battery (12V)                      |       ✔       |   ✔    |         ✔         |            
| Oil                                |       ✔       |   ✔    |         ✔         |   
| Tire Pressure                      |       ✔       |   ✔    |         ✔         |            
| GPS/Location Data (JSON)           |       ✔       |   ✔    |         ✔         |                 
| Alarm Status                       |       ✔       |   ✔    |         ✔         |
| Status Ignition                    |       ✔       |   ✔    |         ✔         |          
| Status Door                        |       ✔       |   ✔    |         ✔         |              
| Window Position                    |       ✔       |   ✔    |         ✔         |    
| last refresh (timestamp)           |       ✔       |   ✔    |         ✔         |
| Speed                              |       ✔       |   ✔    |         ✔         |
| Gear Lever Position                |       ✔       |   ✔    |         ✔         |
| Indicators/Warnings                |       ✔       |   ✔    |         ✔         |
| Temperature Coolant                |       ✔       |   ✔    |         ✔         |
| Temperature Outdoors               |       ✔       |   ✔    |         ✔         |
| RC: Status Remote Start[^1][^2]    |       ✔       |   ✔    |         ✔         |
| RC: Remaining Duration[^1][^2]     |       ✔       |   ✔    |         ✔         |
| FordPass Messages                  |       ✔       |   ✔    |         ✔         |
| Belt Status                        |       ✔       |   ✔    |         ✔         |
| (Deep)Sleep Mode                   |       ✔       |   ✔    |         ✔         |
| Revolution / Engine Speed          |       ✔       |   ✔    |         ?         |
| Fuel Level (can be > 100%)         |       ✔       |   ✔    |                   |
| Temperature Engine Oil             |       ✔       |   ✔    |                   |
| Status Diesel System               |       ✔       |   ✔    |                   |
| AdBlue Level                       |       ✔       |   ✔    |                   |
| EV-Data collection                 |               |   ✔    |         ✔         |
| EV Plug Status                     |               |   ✔    |         ✔         |
| EV Charging information            |               |   ✔    |         ✔         |
| State of Charge (SOC)              |               |   ?    |         ✔         |
| EV Energy Consumption (last trip)  |              |   ?    |         ✔         |
| EV Last Charging Session           |              |   ?    |         ✔         |
| EVCC status code ('A', 'B' or 'C') |               |   ?    |         ✔         |
| Yaw Rate                           |       ✔       |   ✔    |         ✔         |
| Acceleration (X-Axis               |       ✔       |   ✔    |         ✔         |
| Status Brake Pedal                 |       ✔       |   ✔    |         ✔         |
| Brake Torque                       |       ✔       |   ✔    |         ✔         |
| Accelerator Pedal Position (%)     |       ✔       |   ✔    |         ✔         |
| Status Parking Brake               |       ✔       |   ✔    |         ✔         |
| Torque at Transmission             |       ✔       |   ✔    |         ✔         |  
| Status Wheel Torque                |       ✔       |   ✔    |         ✔         |
| Cabin Temperature                  |       ✔       |   ✔    |         ✔         |

Many sensors provide more detail information as attributes of sensors. These attributes are available by expanding the panel at the bottom of the sensor view (marked by green border).

![image](https://raw.githubusercontent.com/marq24/ha-fordpass/refs/heads/main/images/012.png)

You can find more details about the individual sensors when accessing your HA via `http://[your-ha-ip-here]/developer-tools/state` and then selecting the individual sensor from the dropdown list, then you can see all the attributes of the sensor.

Based on these attributes, you can create your own template sensors or automations in Home Assistant.


## Buttons / Switches / Other

| Type                | Sensor Name                                         | Petrol/Diesel | (P)HEV/BEV |
|:--------------------|:----------------------------------------------------|:-------------:|:----------:|
| DeviceTracker       | Vehicle Tracker[^1]                                 | ✔             | ✔          |

[^1]: Must be supported by the vehicle. If not supported, the entity will not be available in the UI.
[^2]: _RC_ stands for 'Remote Control'.
[^3]: There are four controls — one for each seat. Depending on your vehicle configuration, you can select 'Heating Level I-III' and 'Cooling Level I-III' for each seat individually. Please note that not all vehicles support the full set of featured (e.g., only heating) and/or that there might be only the front seats available.
[^4]: The 'Start charging' button will only work with supporting charging stations (wallboxes) - e.g., Ford Charge Station Pro (FCSP), and only if the vehicle is plugged in. If the vehicle is not plugged in, the button will be disabled.
[^5]: Once the charging process has been started, the switch allows you to pause and unpause the charging process. It's not possible to actually start a charging session via this switch — you must use the _EV Start_-button for this! The switch will be toggled to `ON` when the vehicle is plugged in and the wallbox has started to charge the car. When you toggle the switch `OFF`, the charging process will be paused, and when you toggle it `ON` again, the charging process will resume.
[^6]: In FordPass™ App you can create _Target Charge Locations_ — Based on the previous DC charging locations (this functionality was also new for me).<br/>
   This integration will create up to three select entities — one for the first three of these locations. You can select the target charge level for each of these locations [some sort of strange option list: 50%, 60%, 70%, 80%, 85%, 90%, 95% & 100%]. The target charge level will be used when you start a charging session, e.g., via the _EV Start_-button.
   If you don't have any target charge locations configured in FordPass™, then this entity will not be available in Home Assistant.<br/>
   The entities for the second and third 'charge locations select'-entities are disabled by default, but you can enable them in the integration.


## Want to report an issue?

Please use the [GitHub Issues](https://github.com/marq24/ha-fordconnect-query/issues) for reporting any issues you encounter with this integration. Please be so kind before creating a new issues, check the closed ones if your problem has been already reported (& solved).

To speed up the support process, you might like to already prepare and provide DEBUG log output. In the case of a technical issue, I would need this DEBUG log output to be able to help/fix the issue. There is a short [tutorial/guide 'How to provide DEBUG log' here](https://github.com/marq24/ha-senec-v3/blob/main/docs/HA_DEBUG.md) — please take the time to quickly go through it.

For this integration, you need to add:
```
logger:
  default: warning
  logs:
    custom_components.fordconnect_query: debug
```

### Additional considerations before reporting an issue

If you miss entities or functionality, please check if there is any data available in the FordPass™/The Lincoln Way™ App. If there is no data available in the FordPass™/The Lincoln Way™ App, then there might be good reasons why there is no data available for this integration either. Please be aware that not all vehicles support all features, so it's possible that some entities are not available for your vehicle.

You can enable the __Log API responses to local HA filesystem__ in the integration configuration. This will log all API responses to the local HA filesystem, which can be helpful for any data debugging purposes. The log files will be stored in the `.storage/fordconnect_query/data_dumps` directory of your Home Assistant installation.

![image](https://raw.githubusercontent.com/marq24/ha-fordpass/refs/heads/main/images/011.png)

When you create an issue, please consider:
- the data can contain sensitive information  do not post any of the files in the issue.
- you can email me the files directly (please include a link to the GitHub issue).


## I need You!

In the past month I have asked various Ford owners to support the development of this integration by providing access to their vehicle data. This has helped a lot to improve the integration and to ensure that it works with various Ford models (EV's, PHEV's, Petrol and Diesel vehicles).

Currently, I do have (IMHO) enough different vehicles to test the integration. If this situation is going to change, I will ask again for your support – typically in the [discussion area of this repository](https://github.com/marq24/ha-fordconnect-query/discussions).

In the meantime, it would be very kind if you would consider supporting the ongoing development efforty by a donation [via revolut][revolut] | [via wero][wero] | [via paypal][paypal], [buying some coffee][buymecoffee] or become [a GitHub sponsor][ghs], where the last one is my personal favourite.


## Supporting the development
If you like this integration and want to support the development, please consider supporting me on [![github][ghsbadge]][ghs] [![Wero][werobadge]][wero] [![Revolut][revolutbadge]][revolut] [![PayPal][paypalbadge]][paypal] [![BuyMeCoffee][buymecoffeebadge]][buymecoffee]



## Credits
- [@crowedavid](https://github.com/crowedavid) — David, who is great support here in the community and has provided a lot of feedback and ideas for improvements. Also, he has provided various HA automations and template sensors for this integration. Thanks a lot for your support David!


[hacs]: https://hacs.xyz
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge&logo=homeassistantcommunitystore&logoColor=ccc

[ghs]: https://github.com/sponsors/marq24
[ghsbadge]: https://img.shields.io/github/sponsors/marq24?style=for-the-badge&logo=github&logoColor=ccc&link=https%3A%2F%2Fgithub.com%2Fsponsors%2Fmarq24&label=Sponsors

[buymecoffee]: https://www.buymeacoffee.com/marquardt24
[buymecoffeebadge]: https://img.shields.io/badge/buy%20me%20a-coffee-blue.svg?style=for-the-badge&logo=buymeacoffee&logoColor=ccc

[buymecoffee2]: https://buymeacoffee.com/marquardt24/membership
[buymecoffeebadge2]: https://img.shields.io/badge/coffee-subs-blue.svg?style=for-the-badge&logo=buymeacoffee&logoColor=ccc

[paypal]: https://paypal.me/marq24
[paypalbadge]: https://img.shields.io/badge/paypal-me-blue.svg?style=for-the-badge&logo=paypal&logoColor=ccc

[wero]: https://share.weropay.eu/p/1/c/6O371wjUW5
[werobadge]: https://img.shields.io/badge/_wero-me_-blue.svg?style=for-the-badge&logo=data:image/svg%2bxml;base64,PHN2ZwogICByb2xlPSJpbWciCiAgIHZpZXdCb3g9IjAgMCA0Mi4wNDY1MDEgNDAuODg2NyIKICAgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIgo+CiAgPGcKICAgICBjbGlwLXBhdGg9InVybCgjY2xpcDApIgogICAgIHRyYW5zZm9ybT0idHJhbnNsYXRlKC01Ny4zODE4KSI+CiAgICA8cGF0aAogICAgICAgZD0ibSA3OC40MDUxLDMwLjM1NzQgYyAwLDAgLTAuMDE4NSwwIC0wLjAyNzgsMCAtNC4zMTg0LDAgLTcuMzQ2MiwtMi41NzY5IC04LjY0NjEsLTUuOTg4NyBIIDk5LjA2OTggQyA5OS4zMDU3LDIzLjA4NDkgOTkuNDI4MywyMS43NzExIDk5LjQyODMsMjAuNDQxIDk5LjQyODMsOS43NTY3MyA5MS43Mzc1LDAuMDEzODc4NyA3OC40MDUxLDAgdiAxMC41MjcgYyA0LjM0MzksMC4wMTE2IDcuMzQxNiwyLjU4MzcgOC42Mjc2LDUuOTg4NyBoIC0yOS4yOTcgYyAtMC4yMzM2LDEuMjgzNyAtMC4zNTM5LDIuNTk3NiAtMC4zNTM5LDMuOTI3NiAwLDEwLjY5MTMgNy43MDAyLDIwLjQ0MzQgMjAuOTk1NSwyMC40NDM0IDAuMDA5MywwIDAuMDE4NSwwIDAuMDI3OCwwIHYgLTEwLjUyNyB6IgogICAgICAgZmlsbD0iI2UyZTNlMyIvPgogICAgPHBhdGgKICAgICAgIGQ9Im0gNzguMzc3NCw0MC44ODQ0IGMgMC40NTEsMCAwLjg5NTEsLTAuMDEzOSAxLjMzNDYsLTAuMDM0NyAyLjcwMTcsLTAuMTM2NSA1LjE1MzUsLTAuNjgwMSA3LjMzOTMsLTEuNTU2NyAyLjE4NTgsLTAuODc2NyA0LjEwNTcsLTIuMDgxOCA1LjczODcsLTMuNTM5MSAxLjYzMywtMS40NTczIDIuOTgxNSwtMy4xNjQzIDQuMDI3LC01LjA0NDkgMC45NTA2LC0xLjcwOTQgMS42NDQ1LC0zLjU1OTkgMi4wNzk0LC01LjQ5MTMgSCA4Ni42NzIgYyAtMC4yNDk4LDAuNTE1OCAtMC41NDEzLDEuMDA4NSAtMC44NzQ0LDEuNDY4OCAtMC40NTU2LDAuNjI5MSAtMC45ODk5LDEuMjAwNSAtMS41OTYsMS42OTMyIC0wLjYwNiwwLjQ5MjcgLTEuMjg2LDAuOTA5IC0yLjAzNTQsMS4yMzA2IC0wLjc0OTUsMC4zMjE1IC0xLjU2NiwwLjU0ODIgLTIuNDQ5NSwwLjY2MTUgLTAuNDMwMywwLjA1NTUgLTAuODc0NCwwLjA4NzkgLTEuMzM0NywwLjA4NzkgLTIuNzUwMiwwIC00Ljk3NzYsLTEuMDQ3OCAtNi41NjY3LC0yLjY4NzggbCAtNy45NDc2LDcuOTQ3OCBjIDMuNTM2NiwzLjIyOTIgOC40NDI2LDUuMjY0NyAxNC41MTY2LDUuMjY0NyB6IgogICAgICAgZmlsbD0idXJsKCNwYWludDApIgogICAgICAgc3R5bGU9ImZpbGw6dXJsKCNwYWludDApIiAvPgogICAgPHBhdGgKICAgICAgIGQ9Ik0gNzguMzc3NywwIEMgNjcuMTAxNiwwIDU5Ljg1MDIsNy4wMTMzNyA1Ny45MDcyLDE1LjY2OTEgSCA3MC4wOTcgYyAxLjQ1NzIsLTIuOTgxNyA0LjMyNzcsLTUuMTQyMSA4LjI4MDcsLTUuMTQyMSAzLjE1MDMsMCA1LjU5NTIsMS4zNDYyIDcuMTkzNSwzLjM4MTggTCA5My41OTA1LDUuODg5MiBDIDkwLjAwNzYsMi4zMDE1NSA4NC44NTY1LDAuMDAyMzEzMTIgNzguMzc1MywwLjAwMjMxMzEyIFoiCiAgICAgICBmaWxsPSJ1cmwoI3BhaW50MSkiCiAgICAgICBzdHlsZT0iZmlsbDp1cmwoI3BhaW50MSkiIC8+CiAgPC9nPgogIDxkZWZzPgogICAgPGxpbmVhckdyYWRpZW50CiAgICAgICBpZD0icGFpbnQwIgogICAgICAgeDE9IjkyLjc0MzY5OCIKICAgICAgIHkxPSIxOC4wMjYxOTkiCiAgICAgICB4Mj0iNzQuNzU0NTAxIgogICAgICAgeTI9IjQwLjMxMDIiCiAgICAgICBncmFkaWVudFVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+CiAgICAgIDxzdG9wCiAgICAgICAgIG9mZnNldD0iMC4wMiIKICAgICAgICAgc3RvcC1jb2xvcj0iI0UyRTNFMyIKICAgICAgICAgc3RvcC1vcGFjaXR5PSIwIi8+CiAgICAgIDxzdG9wCiAgICAgICAgIG9mZnNldD0iMC4zOSIKICAgICAgICAgc3RvcC1jb2xvcj0iI0UyRTNFMyIKICAgICAgICAgc3RvcC1vcGFjaXR5PSIwLjY2Ii8+CiAgICAgIDxzdG9wCiAgICAgICAgIG9mZnNldD0iMC42OCIKICAgICAgICAgc3RvcC1jb2xvcj0iI0UyRTNFMyIvPgogICAgPC9saW5lYXJHcmFkaWVudD4KICAgIDxsaW5lYXJHcmFkaWVudAogICAgICAgaWQ9InBhaW50MSIKICAgICAgIHgxPSI2MS4yNzA0MDEiCiAgICAgICB5MT0iMjMuMDE3Nzk5IgogICAgICAgeDI9Ijc5Ljc1NDUwMSIKICAgICAgIHkyPSI0LjUzNDI5OTkiCiAgICAgICBncmFkaWVudFVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+CiAgICAgIDxzdG9wCiAgICAgICAgIG9mZnNldD0iMC4wMiIKICAgICAgICAgc3RvcC1jb2xvcj0iI0UyRTNFMyIKICAgICAgICAgc3RvcC1vcGFjaXR5PSIwIi8+CiAgICAgIDxzdG9wCiAgICAgICAgIG9mZnNldD0iMC4zOSIKICAgICAgICAgc3RvcC1jb2xvcj0iI0UyRTNFMyIKICAgICAgICAgc3RvcC1vcGFjaXR5PSIwLjY2Ii8+CiAgICAgIDxzdG9wCiAgICAgICAgIG9mZnNldD0iMC42OCIKICAgICAgICAgc3RvcC1jb2xvcj0iI0UyRTNFMyIvPgogICAgPC9saW5lYXJHcmFkaWVudD4KICAgIDxjbGlwUGF0aAogICAgICAgaWQ9ImNsaXAwIj4KICAgICAgPHJlY3QKICAgICAgICAgd2lkdGg9IjE3Ny45MSIKICAgICAgICAgaGVpZ2h0PSI0MSIKICAgICAgICAgZmlsbD0iI2ZmZmZmZiIKICAgICAgICAgeD0iMCIKICAgICAgICAgeT0iMCIgLz4KICAgIDwvY2xpcFBhdGg+CiAgPC9kZWZzPgo8L3N2Zz4=

[revolut]: https://revolut.me/marq24
[revolutbadge]: https://img.shields.io/badge/_revolut-me_-blue.svg?style=for-the-badge&logo=revolut&logoColor=ccc

[hainstall]: https://my.home-assistant.io/redirect/config_flow_start/?domain=fordconnect_query
[hainstallbadge]: https://img.shields.io/badge/dynamic/json?style=for-the-badge&logo=home-assistant&logoColor=ccc&label=usage&suffix=%20installs&cacheSeconds=15600&url=https://analytics.home-assistant.io/custom_integrations.json&query=$.fordconnect_query.total
