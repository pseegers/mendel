mendel
============================

<img src="http://t2.gstatic.com/images?q=tbn:ANd9GcStFW16rQWHvY4hF1me2nO5K3KmMHPoHdS_MmrnhkEv1W1dAl3qrw" width="60px"> I can deploy almost any Java service
-------------------------------------

After careful study of dozens of Java services at Sprout Social, I have bred out the undesirable traits of miscreant services' myriad deployment mechanisms.

* follows `sprout_java` conventions
* supports uberjars, tar.gz archives, jdeb Debian Packages (central apt repo or .deb files)
* uses symlinks to switch between deployed versions
* supports rollbacks, to any prior version
* track deployments in Graphite via http://yourgraphitehost/events/
* runs tests first (via `maven package`)
* supports services managed by [upstart](http://upstart.ubuntu.com/)
* configuration file driven (no more writing `fabfile.py`)
* extendable/customizable if you *really* need it

get it!
-------
**mendel** is available in pypi. You'll likely want to install **mendel** globally:

```
sudo pip install fabric-mendel
```

synopsis
---------
```
$ mendel --list
Available commands:

    build                [advanced]	builds new application bundle for your service using maven
    deploy               [core]		builds, installs, and deploys to all the specified hosts
    dev                  [hosts] 	sets deploy hosts to 127.0.0.1
    init                 [core]		Prepare an existing project to be deployed by mendel.
    install              [advanced]	install latest build on the hosts you specify
    link_latest_release  [advanced]	cowboy it -- Links the most recent release into current
    rollback             [core]		choose a version to rollback to from all available releases
    tail                 [core]		watch the logs
    upload               [advanced]	upload your bundle to the server
    upstart              [advanced]	'start', 'stop', 'restart', or get the 'status' of your service
```

examples
--------

There are 4 working examples inside this repository, each with a Vagrant file that replicates the initial environment bootstrapped by the `sprout_java` LWRP. Checkout the `README.md`s in each example:

* **uberjar**: ./examples/java/jar
* **tar.gz**: ./examples/java/tgz
* **deb pkg**: ./examples/java/deb
* **remote deb**: ./examples/java/remote_deb

bootstrap an existing project
-------------------------------------

in this case, we'll bootstrap an uberjar service (most common at sprout).change directories into your java project, and then:

```
$ mendel init
enter service name: myservice
enter bundle_type type (jar, tgz, deb) [jar]:
enter project_type type (java) [java]:

Done.
```

```
$ cat mendel.yml
service_name: myservice
bundle_type: jar
project_type: java
hosts:
  dev:
    hostnames: 127.0.0.1
    port: '2222'
```

This will create a `mendel.yml` file in your current directory. `mendel init` should be executed in the root of your java project (where your `pom.xml` is located).

deploying
---------

Mendel looks for a config file in the root of your project, `mendel.yml`. Let's say you have some service, `myservice` and your unit of deployment is an uberjar. You might have a `mendel.yml` like this:

```
service_name: myservice
bundle_type: jar
project_type: java
hosts:
  # production environment
  prod:
    hostnames: myservice01,myservice02,myservice03
  # your local environment, likely a Vagrant VM
  dev:
    hostnames: 127.0.0.1
    port: 2202
```

Then you can deploy like this:

```
mendel prod deploy
```

rolling back
------------

Assuming the aforementioned example config, rollback is also simple:

```
mendel prod rollback
[myservice01] Executing task 'rollback'
20150629-235124-stantonk-fbc45d96810a
20150804-162857-stantonk-0c837d1e88b2
20150810-204318-stantonk-083a01b082ff
20150811-014510-stantonk-82aba3fdfcf0
20150812-203810-stantonk-98b2551a7e4b
20150929-170509-stantonk-57689043b8b1
20151002-221440-stantonk-57689043b8b1+
20151002-221652-stantonk-57689043b8b1+
20151002-222044-stantonk-57689043b8b1+
20151002-222509-stantonk-57689043b8b1+
20151002-222940-stantonk-57689043b8b1+
20151002-223716-stantonk-57689043b8b1+
20151002-223935-stantonk-57689043b8b1+
20151103-002011-stantonk-5ffd6738e751 <-- current
Rollback to: [20151002-223935-stantonk-57689043b8b1+]
```

All previous deployed builds are on the server so you can rollback to whichever you choose. Of course, this is not foolproof (since you have to select the same version to rollback to on each of the nodes the service is deployed to). But eventually we will allow for artifacts to be pulled from an artifact repository.

deployment tracking
-------------------
Deployment tracking is done **automatically** for you.

*View timeline of deployments; who, what, when, where:*
![track-deploys](docs/track-deploys.png)

*Plot deployments in Graphite Dashboards against other metrics you're tracking in your application:*
![plot-deploys](docs/plot-deploys.png)

more examples
--------
```
-f == use specific config file. useful if more that one service uses same jar file and jar_name is in config file.
mendel -f mendel_tagger.yml prod deploy


-H == specify host/hosts -H host1,host2
mendel -H message01 deploy


everything but service restart (good way to verify config)
mendel prod build upload install
```

Conventions you must follow
---------------------------
Use `sprout_java` in Chef. In other words:

1. Make sure your service is upstarted and has its own user and group, where servicename==user==group.
2. Make sure your service's upstart.conf points to
   `/srv/service-name/current`
3. Make sure your service's logs are set to go to `/var/log/service-name/`, or make sure your log4j.properties file puts them into `/srv/service-name` or really anywhere besides in the root of your classpath because each deployment will move a symlink.

Future
------

* java service maven archetype(s) that sets people up for success!
* Support other languages (only variance is build command, test running/discovery and where to grab bundle from)
* discovery of target hosts for deployment *from* Chef instead of static config file.
* support bootstrapping an application onto a host w/o Chef (maybe?), this is also really easy to add (Mesos?)

Open Questions
--------------
* How do we handle services that have data that persists across deployments, for example, tailers have lastReadFiles. Simplest solution is to just assume that application state lives in `/srv/service_name`, which means local developers need to make those directories probably, as would CI/jenkins..nbd tho I don't think. The Linux convention according to [Linux Filesystem Hierarchy Version 0.65](http://tldp.org/LDP/Linux-Filesystem-Hierarchy/html/Linux-Filesystem-Hierarchy.html) is `/var/lib/service_name`. [Spotify](https://github.com/spotify/helios/blob/master/src/deb/helios-master/postinst) follows the Linux Filesystem Hierarchy convention it seems, and they also are using [jdeb](https://github.com/tcurdt/jdeb) to pacakge their services in to debian packages.
* There arguably is a need for decoupling deployment from building, insofar as sometimes, you are simply provisioning additional server resources to horizontally scale an existing service, and no new builds are required -- in this event, you want to be able to deploy the *exact* same release to the newly provisioned servers as is running on existing services. Amazon S3 is a natural choice for this, as would potentially be Archiva (but seems more painful). Ideally we would write a pure-python S3 implementation to avoid having to install a python s3 pip package in order to run the fab file. My thought on approach to this is that during the *install* phase of deployment, instead of just putting the application bundle directly on the server, place it into S3 first, and redownload it to the local machine, and *then* ship it over. That way we avoid having to create some sort of "deploy agent" that runs on all of our servers. Or maybe it is possible to wget the archive from S3 through fabric w/o needing. Then we would have all revisions available in a central location for installing to newly provisioned hardware.
