# ds-easyconf
With 389ds > 1.4 the LDAP browser has been removed. A new console is integrated in cockpit and new command line tools perform the configuration.

With dscreate you can read some configuration from a inf file, but this is a little set of parameters.

Because you could have many instances and many dbs, it could be difficult to maintain all configuration as well and you must call `dsconf` (or the equivalent `ldapmodify` operations) many times.

With `ds-easyconf` you can provide all configuration parameters in a single **yaml** file. Simply run `ds-easyconf -h <ldapserver>` to fully configure your 389ds instance.

The configuration file provides **yaml** block corresponding to the dsconf parameters. To better understand you can see at the conf.dist file provided by default. Here you have one instance and two multimaster servers.

The only exception at the above gerarchy is in `repl-agmt` --> `create`, which could be followed by the server name (fqdn) where install the children replication agreements. The same idea is used to find out the replica-id and the instances allowed on each server you provide.

When you provide the server name with the `-h` switch, `ds-easyconf` will configure only the instances expected by conf in that server, with the corresponding replica-id and agreements.

## INSTALL
On Centos/RHEL 8 simply create the repo:

```
curl -1sLf \
  'https://dl.cloudsmith.io/public/csi/dseasyconf/cfg/setup/bash.rpm.sh' \
  | sudo -E bash
```

If you have a modular python, you may have to add

`module_hotfixes=true`

under

`[csi-dseasyconf]` section of `/etc/yum.repos.d/csi-dseasyconf.repo`.

Then run

`dnf install python3-ds-easyconf`

## RUN

Now you can modify your `/etc/ds-easyconf/ds-easyconf.conf` and run

```ds-easyconf -h <server to configure>```

You can add multiple `-i <instance name>` if you want to configure only some instances listed on the config file.
