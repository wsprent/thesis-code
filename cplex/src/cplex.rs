
mod internal {
    #![allow(non_upper_case_globals)]
    #![allow(non_camel_case_types)]
    #![allow(non_snake_case)]

    include!(concat!(env!("OUT_DIR"), "/bindings.rs"));
}

use self::internal::CPXENVptr;

pub struct Cplex {
    env: CPXENVptr,
}

pub fn get_cplex() -> Result<Cplex, String> {
    let (env, status) = unsafe {
        let mut status : i32 = -10;
        let env = internal::CPXopenCPLEX(&mut status);
        (env, status)
    };
    if status == 0 {
        return Ok(Cplex { env: env });
    } else {
        return Err(format!("Could not open CPLEX - status {}.", status));
    }
} 
