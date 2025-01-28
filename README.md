# Underground PM

Privacy hosting

## Dependencies

* python
* pip
* npm
* libvirt
* postgresql
* nginx
* monero
* openrc/systemd

## Installing

Clone repository and download submodules:

```
git submodule init
git submodule update
```

## Setup

### App

Define environment varibles in `/etc/environment`

```
HOST=127.0.0.1
PORT=8000

DATABASE_URL=postgresql://user:password@localhost/dbname

IMAGES_PATH=/var/lib/libvirt/images

VDS_DAYS=31
VDS_MAX_PAYED_DAYS=90
VDS_EXPIRED_DAYS=3

MONERO_RPC_IP=127.0.0.1
MONERO_RPC_PORT=20000
MONERO_RPC_USERNAME=username
MONERO_RPC_PASSWORD=password
MONERO_RPC_LOG_PATH=/dev/null

MONERO_WALLET_PATH=/var/lib/wallets/underground
MONERO_WALLET_PASSWORD=password
MONERO_DAEMON_ADDRESS=127.0.0.1:18081
MONERO_TX_PATH=underground_checkout
```

Install noVNC dependencies

```
cd underground/static/noVNC
npm i
```

Install requirements and build the app

```
python -m venv venv
. venv/bin/activate
pip install .
pyproject-build --wheel
```

Install the app

`pip install dist/underground.pm-*-py3-none-any.whl --break-system-packages`

### Postgresql

Execute it in Postgres shell

```
CREATE USER underground WITH PASSWORD 'underground';
CREATE DATABASE underground;
ALTER USER underground CREATEDB;
ALTER DATABASE underground OWNER TO underground;
GRANT ALL PRIVILEGES ON DATABASE underground TO underground;
```

### Nginx

```
cp contrib/nginx/sites-available/underground.pm.conf /etc/nginx/sites-available/underground.pm.conf
ln -s /etc/nginx/sites-available/underground.pm.conf /etc/nginx/sites-enabled/underground.pm.conf
```

Edit `/etc/nginx/nginx.conf`

```
http {
    ...

    limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;
    limit_req_zone $binary_remote_addr zone=register:10m rate=1r/m;

    ...
}
```

### Monero

`cp contrib/monero/monero_wallet_rpc_run /bin`
`cp contrib/monero/monero_test_wallet_rpc_run /bin`

### OpenRC

```
cp contrib/openrc/underground.pm /etc/init.d/underground.pm
cp contrib/openrc/monero-wallet-rpc /etc/init.d/monero-wallet-rpc
cp contrib/openrc/monero-wallet-rpc /etc/init.d/monero-test-wallet-rpc
```

### Systemd

```
cp contrib/systemd/underground.pm.service /etc/systemd/system/underground.pm.service
cp contrib/systemd/monero-wallet-rpc.service /etc/systemd/system/monero-wallet-rpc.service
cp contrib/systemd/monero-test-wallet-rpc.service /etc/systemd/system/monero-test-wallet-rpc.service
```


## Start

### OpenRC

```
rc-update add sshd default
rc-update add libvirtd default
rc-update add postgresql default
rc-update add nginx default
rc-update add monerod default
rc-update add monero-wallet-rpc default
rc-update add underground.pm default

rc-service sshd start
rc-service libvirtd start
rc-service postgresql start
rc-service nginx start
rc-service monerod start
rc-service monero-wallet-rpc start
rc-service underground.pm start
```

### Systemd

`systemctl enable --now sshd libvirtd postgresql nginx monerod monero-wallet-rpc underground.pm`


## Testing

Define environment varibles for test wallet in `/etc/environment`

```
MONERO_TEST_RPC_PORT=20000
MONERO_TEST_RPC_USERNAME=username
MONERO_TEST_RPC_PASSWORD=password
MONERO_TEST_RPC_LOG_PATH=/dev/null

MONERO_TEST_WALLET_PATH=/var/lib/wallets/underground.pm
MONERO_TEST_WALLET_PASSWORD=password
MONERO_TEST_DAEMON_ADDRESS=127.0.0.1:18081
MONERO_TEST_TX_PATH=underground_checkout
```

Install requirements and build the app

`pip install .[dev]`

Run test wallet

`rc-service monero-test-wallet-rpc start`

or

`systemctl start monero-test-wallet-rpc`


Run tests

`pytest`
