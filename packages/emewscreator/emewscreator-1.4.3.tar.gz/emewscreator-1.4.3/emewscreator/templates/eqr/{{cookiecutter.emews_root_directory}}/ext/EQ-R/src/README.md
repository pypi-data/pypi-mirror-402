# EQ-R
EMEWS Queues - R implementation

EQ-R is a Swift/T (http://swift-lang.org/Swift-T/) extension that
allows Swift/T workflows to communicate with a persistent embedded R interpreter
on a worker process via blocking queues. Using the mechanism an R model
exploration (ME) algorithm can be used to control and define an ensemble
of model runs.

## Compiling EQ-R

Compiling EQ-R is a 3 step process.

Prerequisites
-------------
* The RInside and Rcpp packages R packages. These can be installed
using R's `install.packages` command from within R.

Outline
-------

The compilation is run from the command and consists of the following
3 steps.

```
$ ./bootstrap
$ ./configure
$ make install
```

Details
-------

1. Run ``./bootstrap`` from the command line. This runs ``autoconf`` and generates ``./configure``.
2. Run ``./configure`` followed by any required arguments.  See the ``./configure --help`` output for a list of the arguments to `configure` .  Key
arguments are:
    * `--prefix`: EQR install location. The default of the directectory above this one (e.g., `ext/EQ-R`)
is compatible with EMEWS Creator. Tpically the `prefix` does not need to be set when using EMEWS Creator.
    * `-with-tcl`: Tcl installation root location (e.g., /usr)
    * `--with-r`: R installation root location. 
3. Run ``make install`` to compile the eqr library, create `pkgIndex.tcl`, and copy them and `EQR.swift` 
to the EQR install location. 

To remove the compilation artifacts, use ``make clean`` or ``make distclean``.
