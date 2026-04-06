# dj-auth

dj-auth is an authentication microservice which is fully standalone, requiring minimal configuration to get working and easily deployable 
to allow for more modular systems and less developer work in rolling their own authentication services which are tightly coupled 
to other services they are implementing.

## Authentication services

Services can be found in the `repo_root/auth_pkg/auth_/auth_services/`
- [X] Session-based authentication service
- [X] JSON Web Token-based authentication service
- [ ] OAuth authentication service
- [ ] E-Mail Verification

## Setup

```bash
# Clone the repo
git clone git@github.com:bitflaw/dj-auth
cd dj-auth
```

### Environment variables:

```bash
SECRET_KEY
DEBUG               #default = False
ALLOWED_HOSTS

REDIS_HOST          #default = localhost    # IF USING DOCKER COMPOSE, change this to 'cache'
REDIS_PORT          #default = 6379
REDIS_RDECODE       #default = True
REDIS_TTL           #default = 3600 (s)

DB_ENGINE           #default = postgresql
DB_NAME 
DB_USER
DB_PASSWD
DB_HOST             #default = localhost    # IF USING DOCKER COMPOSE, change this to 'db'
DB_PORT             #default = 5432
```

### Running
#### To run locally (non-docker),
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd auth_pkg
python manage.py runserver
```

#### With Docker:
If you already have a redis server running and a database running, just use the Dockerfile provided to create an image and run it:
```bash
docker build -t [IMAGE-NAME] .
docker run [IMAGE-NAME]
```

Otherwise, you can use the `docker-compose.yml` file to spin up the server instance, the redis instance and a database instance too.
```bash
docker compose up
```

## Endpoints

- `login`: logs a user in, stores an instance of the user object together with the token (for JWT -> access_token, for session -> session_id)
            in the redis cache where they will live for `REDIS_TTL` time or until logout is triggered.
- `verify_token`: Verifies whether the current token you have is valid, based on whether they are in the redis cache and expiry time.
- `refresh_token` : specific only to JWTAuthService. Used to provide a new access token from a valid refresh token.
- `logout`: Used to logout a user. Will delete them from the cache and delete all their tokens.

>[!NOTE]
> All tokens are and are expected to be stored in cookies.
> To access the cache from other services, make sure to set the same redis environmental
> variables in those services too. IE `REDIS_HOST`, `REDIS_PORT`, `REDIS_TTL`, and `REDIS_RDECODE`

## For those using django or DRF in other services:

A helper class has been provided in the `dj-external/AuthService.py` file in the source tree. This has been created to take advantage
of the `DEFAULT_AUTHENTICATION_CLASSES` setting in `settings.py` where this class can be specified as a default authentication class.
`AUTH_MS_DOMAIN` env variable will be needed for this class, as well as the redis env variables specified above.
This specifies the domain of the auth microservice.

Also, if using a shared database for all your services (this microservice was built with that in mind) then **DO NOT** create your own
User class as this microservice already creates it, and is built around it. instead do the following:
```bash
python manage.py inspectdb auth__user   # assumes migrations were already ran, if not, run them
```

and copy the output of this command into your `models.py`.
This gives you a User table to work with in your development, one which does not affect the real table at all.
To make any modifications to the User table, please do them in the `models.py` file in this microservice. A
User class inheriting from the `AbstractUser` class. Note that you will have to regenerate it again if you make changes
to the actual table (or map the change manually).
