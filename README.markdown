# Micropress #

Micropress is a python-based tool for building static websites. It brings together a number of modern web technologies to facilitate rapid development. At its core, micropress render individual HTML pages from  [markdown][] source using [jinja2][] templates. Additional "resources" such as javascript,css, and images can be included as well, which are either included directly or built from alternative sources. Standard micropress extensions include support for [coffeescript][] and [less][].

[markdown]:http://daringfireball.net/projects/markdown/
[jinja2]:http://jinja.pocoo.org/docs/
[coffeescript]:http://jashkenas.github.com/coffee-script/
[less]:http://lesscss.org/

## Why Static? ##

Static sites are simple to deploy, cheap to host, and easy to scale. Modern web technologies allow for many features of traditional CMS/blog software to be handled by secondary off-site services (for example analytics, comments). Static sites are well suited to small/medium sites that are for people, organizations, or projects that need to be built and deployed rapidly with a light footprint. 

# Building a Site #

A site is built from a canonical directory structure which has the following layout

* site.yaml - [yaml][] file describing site configuration and metadata
* pages/ - markdown files constituting the source of a html file
* css/ - CSS files (`.css` or `.less`) files
* js/ - javascript files (`.js` or `.coffeescript`)
* templates/ - jinja2 templates for rendering html. Templates have the `.tmpl` extension
* resources/ - additional content to include in site. Directly coped into output folder
* site/ - build directory. All output will be placed here. Output directory can be configured

[yaml]:http://www.yaml.org/

## Site Config ##

The `site.yaml` is a [YAML][] structured file which describes metadata about the site. 

* encoding - text encoding of input/output
* domain - url of where this site will be hosted
* root - absolute path where this site will be hosted (defaults to /)
* markdown - configure markdown rendering
* extensions - configured loaded extensions

## Pages ##

Each page in the `pages/` directory should end with either a `.markdown` or `.html` extension. A page is written as a header block followed by a one or more empty lines followed by HTML or markup syntax. Header attributes are specified one-per-line as a key value pair separated by a colon. For example:

    title: This is my page
    property: value
    foo: bar
    
    lorum ipsum zzzz

Header attributes are accessible from templates (see template writing), and some have special meaning. In particular, page attributes that are useful are:

* title - page title, defaults to file name without extension
* tags - comma seperated list of tag values
* category - a category name
* date-created - a formatted date
* template - template used to render page. Defaults to template named "default"

Extensions may rely on other attributes being set.

## Resources ##

Resources are additional files such as javascript and css files that are included with your site. Javascript files are put in the `js/` directory and `css\` files are put in the css directory. Additional resources such as images or external javascript can be placed within the `resources\` directory to include within the site structure.

## Writing Templates ##

Micropress uses the [jinja2][] templating engine for rendering HTML. 

TODO: explain this!

See the [jinja2 template documentation][jinja2-ref] for more details.

[jinja2-ref]:http://jinja.pocoo.org/docs/templates/

# Running Micropress #

To building a site:

   micropress brew [-d outputdir]

This will write everything to an output directory, which is by default called "site"

Micropress allows you to preview your site in am embedded web browser. Changes you make to your site are reloaded on the fly

   micropress preview
      
# Extensions #

Extensions can be configured in the `site.yaml` file

    extensions:
      - myextension

They enable additional technologies. The standard extensions included in micropress are:

* micropress.coffeescript - enables coffeescript files in js directory
* micropress.less - enables less files in css directory
* micropress.notfound - allow you to construct a 404 error document
* micropress.sitemap - allows for generation of a sitemap.xml file
* micropress.rss - allows for generation of a RSS feed file

Consult the individual documentation on these modules for more info

## Writing your own ##

Markdown extensions are standard python modules which export a function hook extend_micropress()

See API docs for more details
