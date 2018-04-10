extern crate bindgen;
extern crate glob;

use glob::glob;

use std::env;
use std::path::PathBuf;

const TYPES : [&'static str; 1] = ["CPXENVptr"];

const FUNCTIONS : [&'static str; 1] = ["CPXopenCPLEX"];

fn main () {
    let mut builder = bindgen::Builder::default()
        // The input header we would like to generate
        // bindings for.
        .header("wrapper.h");

    // Link with cplex
    for prefix in glob("/opt/ibm/ILOG/*/cplex/").unwrap() {
        let prefix = prefix.unwrap();
        for path in glob(&format!("{}/lib/*/static_pic/", prefix.display())).unwrap() {
            match path {
                Ok(libdir) => println!("cargo:rustc-link-search=native={}", libdir.display()),
                Err(e) => println!("{:?}", e)
            }
        }
        builder = builder.clang_arg(format!("-I{}/include/ilcplex", prefix.display()));
    }
    println!("cargo:rustc-link-lib=static=cplex");

    builder = TYPES.into_iter().fold(builder, |b, t| b.whitelist_type(t));
    builder = FUNCTIONS.into_iter().fold(builder, |b, f| b.whitelist_function(f));

    let bindings = builder.generate()
        .expect("Unable to generate bindings");

    // Write the bindings to the $OUT_DIR/bindings.rs file.
    let out_path = PathBuf::from(env::var("OUT_DIR").unwrap());
    bindings
        .write_to_file(out_path.join("bindings.rs"))
        .expect("Couldn't write bindings!");
}
