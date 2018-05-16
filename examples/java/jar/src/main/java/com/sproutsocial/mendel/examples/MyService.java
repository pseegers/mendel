package com.sproutsocial.mendel.examples;

import com.sproutsocial.mendel.examples.resources.HelloResource;
import io.dropwizard.Application;
import io.dropwizard.discovery.DiscoveryBundle;
import io.dropwizard.discovery.DiscoveryFactory;
import io.dropwizard.setup.Bootstrap;
import io.dropwizard.setup.Environment;

public class MyService extends Application<MyConfiguration> {

    public static void main(final String[] args) throws Exception {
        new MyService().run(args);
    }

    @Override
    public String getName() {
        return "mendel-hello-world";
    }

    @Override
    public void initialize(final Bootstrap<MyConfiguration> bootstrap) {
    }

    @Override
    public void run(final MyConfiguration configuration,
                    final Environment environment) {
        environment.jersey().register(new HelloResource());
    }

}
