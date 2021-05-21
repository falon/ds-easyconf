# ds-easyconf
Starting with 389ds > 1.4 the LDAP browser has been removed. Cockpit provides the new console and new commandline tools perform the configuration.

With `dscreate` you can read some configuration parameters from a `inf` file, but this is a little set of parameters.

Because you could have many instances and many dbs, it could be difficult to maintain all configuration and you must call `dsconf` (or the equivalent `ldapmodify` operations) many times.

With `ds-easyconf.py` you can provide all configuration parameters in a single **yaml** file. Simply run `ds-easyconf.py -h <ldapserver>` to fully configure your 389ds instance.

The configuration file provides **yaml** blocks corresponding to the dsconf parameters. To better understand you can see at the *yaml.dist* file provided by default. Here you find one instance and two multimaster servers.

The only exception at the above ierarchy is in `repl-agmt` --> `create`, which could be followed by the server name (fqdn) where install the children replication agreements. The same idea is used to find out the `replica-id` and the instances allowed on each server you provide.

When you provide the server name with the `-h` switch, `ds-easyconf.py` will configure only the instances expected by conf in that server, with the corresponding `replica-id` and *agreements*.


## INSTALL
On Centos/RHEL 8 simply create the repo:

```
curl -1sLf \
  'https://dl.cloudsmith.io/public/csi/dseasyconf/cfg/setup/bash.rpm.sh' \
  | sudo -E bash
```

If you have a modular OS, please enable the 389-ds:

`dnf module enable 389-ds`

Check at the 389ds version, it must be **1.4** or greather.

Then run

`dnf install python3-ds-easyconf`

You can install `ds-easyconf` only on one server which have access to all other ones.

Unfortunately, at least until version **1.4.3.8**, in order to work `dsconf` requires a valid `defaults.inf` file.
 In the remote host you must copy a valid `defaults.inf` from an host where you installed the **389ds**.
 The `defaults.inf` must be placed in the path `/usr/share/dirsrv/inf/`.

## RUN

First, we suppose you create your LDAP instances with `dscreate` on all servers.

Then, in the server where you have installed `ds-easyconf` you can modify your `/etc/ds-easyconf/ds-easyconf.yaml` and run

```ds-easyconf.py -h <server to configure>```

You can add multiple `-i <instance name>` if you want to configure only some instances listed on the config file.

You can specify the config file to read with the `-c` switch. For instance, you can create a config file just to run all
 replication initialization after the complete installation ended.

All commands execute in the config file order. Some interesting points:

- yaml doesn't allow duplicated keys. You can add **key-*n*** where `n` is a number to repeat the same key. The `-n` will be removed.
- `on` and `off` values must be inside quotation marks (ie: `"on"`)
- If you need to set attributes value and name in a single key, don't separate them by spaces:
  - `--attr <name>:` is wrong.
  - `--attr=<name>:` is fine.

## ANSIBLE INTEGRATION
You could add `ds-easyconf.py` in an Ansible play as a command.

Unfortunately `dsconf` is not idempotent. There are some hints in order to run the command many times and obtain always a success status, hovewer.

First, in ldapmodify use `replace` in place of `add`. About `dsconf`, we see a set of errors which happen when the command executes more than one time. Items already existing are not actual errors, but failure because they are already set.
You can add these errors in the **FALSE_ERRORS** var in the yaml config file. A set of predefined errors are configured by default, as you can see looking at *ds-easyconf.yaml*.
Each element is a regular expression. If the command error match any regex, the the *error* is declassified as *warning* and the exit status will stay at `0`.

The exit status of `ds-easyconf.py` is the sum of all errors.
