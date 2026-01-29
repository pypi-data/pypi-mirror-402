# pyramid-traversal-api

**NOTE** This library is currently WIP. Expect breakages, even between minor versions, while on major version 0.

A set of helpers that makes it easier to write traversal-based REST APIs for [pyramid](https://trypyramid.com/) with modern QoL features like

 * Request/response validation
 * Automatic OpenAPI
 * Automatic SQLAlchemy requests
   - But possible to write your own support for any backend
 * An "industry standard" method for dealing with CORS
   - If by industry standard you mean a configurable version of CORS method that "every" Pyramid user uses
 * Built around writing REST APIs

## Design goals

 * Build tools FOR pyramid, not REPLACING pyramid
   - No new abstraction layers on top of Pyramid, just new building blocks
 * Easy to slap on top of an existing project, allowing gradual migration
   - Start small finish big, like Pyramid

## Standing on the shoulder of giants

Thank you to the pylons project for Pyramid. Greetings also go to `Theron Luhn` for [pyramid-marshmallow](https://pypi.org/project/pyramid-marshmallow/), which the OpenAPI functionality of this package is based on.

## Requirements

Python 3.9 or later
