use vecno_addresses::{Address, Prefix};
use vecno_consensus_core::tx::ScriptPublicKey;
use vecno_txscript::{extract_script_pub_key_address, pay_to_address_script};
use pyo3::{pyfunction, PyResult};
use pyo3::exceptions::PyValueError;

#[pyfunction(signature = (prefix, script, version=0))]
pub fn to_address(prefix: &str, script: &str, version: u16) -> PyResult<String> {
    let prefix = Prefix::try_from(prefix).map_err(|_| PyValueError::new_err("Invalid prefix"))?;
    let script_bytes = hex::decode(script).map_err(|_| PyValueError::new_err("Invalid script"))?;
    let address = extract_script_pub_key_address(&ScriptPublicKey::from_vec(version, script_bytes), prefix)
        .map_err(|_| PyValueError::new_err("Invalid script"))?;
    Ok(address.to_string())
}

#[pyfunction]
pub fn to_script(address: &str) -> PyResult<String> {
    let address = Address::try_from(address).map_err(|_| PyValueError::new_err("Invalid address"))?;
    let script = pay_to_address_script(&address).script().to_vec();
    Ok(hex::encode(script))
}
