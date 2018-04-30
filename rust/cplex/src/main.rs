mod cplex;

fn main() {
    let cpx = match cplex::get_cplex() {
        Ok(cpx) => cpx,
        Err(err) => panic!(err)
    };

    println!("Opened CPLEX.");
    println!("Hello, world!");
}
