# myra-eucaptcha

EU captcha protects your website/API against abuse like form spam and credential stuffing.
This package provides server-side verification client for Myra EU Captcha.

## Installation

Installation is performed via the regular PyPi-Repos with 
`pip install myra-eucaptcha` or `uv add myra-eucaptcha`, if you're using the uv package manager.

## Integration

### Frontend

There are only two snippets which need to be included in your page to enable captcha-validation.
This is used to render the captcha and must be placed inside the form you want to protect.

```html
<div class="eu-captcha" data-sitekey="YOUR_MYRA_EUCAPTCHA_SITEKEY"></div>
```

This includes the javascript-part of the captcha, which handles the actual captcha and transmits
captcha data to Myra EU Captcha, updates the displayed Captcha HTML Snippets and adds data to your form.
```html
<script src="https://cdn.eu-captcha.eu/verify.js" async defer></script>
```

Here is a functional, minimalistic example what your page could look like.
```html
    <html>
        <head>
            <title>captcha integration sample</title>
        </head>
        <body>
    
        <form action="/login" method="post">
            <table>
                <tr>
                    <td>user</td>
                    <td>
                        <input type=text name="username" />
                    </td>
                </tr>
                <tr>
                    <td>pass</td>
                    <td>
                        <input type=password name="password" />
                    </td>
                </tr>
                <tr>
                    <td colspan="2">
                        <div class="eu-captcha" data-sitekey="YOUR_MYRA_EUCAPTCHA_SITEKEY"></div>
                    </td>
                </tr>
                <tr><td colspan="2"><input type="submit" name="submit" /></td></tr>
            </table>
        </form>
        
        <script src="https://cdn.eu-captcha.eu/verify.js" async defer></script>
        </body>
    </html>
```



### FastAPI Backend Example

This is the respective backend counterpart for the example-form from above.
The library provides async and sync interfaces via .avalidate() and .validate() respectively.
```python 
from myra_eucaptcha import MyraEuCaptchaClient, MyraEuCaptchaClientConfig

@app.post("/login", response_class=HTMLResponse)
async def login(
    request:Request,
    username: str = Form(...),
    password: str = Form(...),
    eu_captcha_response: str = Form(..., alias="eu-captcha-response"),
):

    # configure the captcha settings and behaviour
    captcha_config = MyraEuCaptchaClientConfig(
        sitekey="YOUR_MYRA_EUCAPTCHA_SITEKEY",
        secret="YOUR_MYRA_EUCAPTCHA_SECRET",
    )

    client = MyraEuCaptchaClient(config=captcha_config)

    # this is depending on your webserver-setup and whether we're behind
    # a reverse-proxy (nginx, apache, traefik, or something similar.)
    remote_addr = request.headers.get('x-real-ip','')
    validationresult = await client.avalidate(
                token=eu_captcha_response,
                remote_addr=remote_addr)

    if validationresult.success:
        # yay - all good.
        # <your-code-here>
        pass
    else:
        # validation failed, check validationresult.errors
        # <your-code-here>
        pass
```


## Design Decisions
The default mode of operation for EU Captcha is permissive and fault-tolerant.
This means, that - should any error occur on the backend side during the communication of your server
and Myra EU Captcha (timeouts, api-errors, network-errors or similar), the validation result will be *True* and no exceptions will be thrown.
The exceptions will however be available in the `MyraEuCaptchaResult.errors` you receive.

This behaviour can be configured, by adapting `MyraEuCaptchaClientConfig`:
```python
    captcha_config = MyraEuCaptchaClientConfig(
        sitekey="YOUR_MYRA_EUCAPTCHA_SITEKEY",
        secret="YOUR_MYRA_EUCAPTCHA_SECRET",
        connect_timeout: int = 3
        read_timeout: int = 10
        write_timeout: int = 10
        pool_timeout: int = 3
        default_result_on_error:bool = True ## this is the validation result, that is returned on exceptions
        suppress_exceptions:bool = True     ## if you want exceptions to be raised, set this to False
    )
```

## Documentation
All documentation regarding non-functional changes, especially integration examples for other frameworks, will be provided and maintained under https://docs.eu-captcha.eu 
Functional changes will be documented in this package with a new release.
