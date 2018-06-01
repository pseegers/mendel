package com.github.Ibracadabra05.resources;

import javax.validation.Valid;
import javax.ws.rs.GET;
import javax.ws.rs.Path;
import javax.ws.rs.Produces;
import javax.ws.rs.QueryParam;
import javax.ws.rs.core.MediaType;

@Produces(MediaType.TEXT_PLAIN)
@Path(("/hello"))
public class HelloResource {

    @GET
    public String getHello(@Valid @QueryParam("name") String name) {
        return "Hello, " + name + "!\n";
    }
}