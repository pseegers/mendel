package com.github.Ibracadabra05.myservice;

import io.dropwizard.Application;
import io.dropwizard.setup.Bootstrap;
import io.dropwizard.setup.Environment;

public class MyServiceApplication extends Application<MyServiceConfiguration> {

    public static void main(final String[] args) throws Exception {
        new MyServiceApplication().run(args);
    }

    @Override
    public String getName() {
        return "MyService";
    }

    @Override
    public void initialize(final Bootstrap<MyServiceConfiguration> bootstrap) {
        // TODO: application initialization
    }

    @Override
    public void run(final MyServiceConfiguration configuration,
                    final Environment environment) {
        // TODO: implement application
    }

}
