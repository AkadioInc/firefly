# FIREfly Extension

A JupyterLab extension which provides a browser for FIREFly data.

# Development

To work on the extension locally you need to [install JupyterLab](https://github.com/jupyterlab/jupyterlab/blob/master/CONTRIBUTING.md#installing-jupyterlab). The guide in the JupyterLab CONTRIBUTING.md worked well. Check JLab runs
before installing the extension: `jupyter lab`.

Once you have JLab running, build and install this extension. From the directory
of this README run:
```
npm install
npm run build
jupyter labextension install
jupyter lab
```

JupyterLab has a watch mode which speed up the iteration time. After building
and install the extension the first time using the above commands, you can
launch the server in watch mode:

```
jupyter lab --watch
```

The server will automatically re-install the extension just files that have changed.
You need only run `npm run build` after editing the extension files.

Note that watch mode *does not* work when adding new files to the extension. You
must re-install the extension when adding new files.


# Deployment

To deploy changes to the extension to the HDFLab cluster test your changes locally,
then run `npm pack`. Copy the generated `firefly-extension-0.0.1.tgz` to the `hdflab-user/`
directory and build a new singleuser docker image.

# Vendor Files

This extensions makes use of newer Phosphor features which are not yet available
in JupyterLab. Since the new features themselves are compatible with the older
version of Phosphor used by JupyterLab, the source files are included in the
`src/vendor/phosphor` directory. Once a new version of JupyterLab is released
with support for the newest Phosphor release, these vendor files can be
removed and the relevant import statements updated.
