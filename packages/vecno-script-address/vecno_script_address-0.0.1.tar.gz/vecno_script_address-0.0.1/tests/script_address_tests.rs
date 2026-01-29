use vecno_script_address::script_address::{to_address, to_script};

const SCRIPT_PAY_TO_PUBKEY: &str = "20e3a134d07b6719befe296576fdea05a14f555f3491b4c13229b7fc77d3aff5b7ac";
const SCRIPT_PAY_TO_PUBKEY_ECDSA: &str = "2103e3100d85efae93e0c2fc654b2f0c33584f213a3fdffd023c821277b21789e064ab";
const SCRIPT_PAY_TO_SCRIPTHASH: &str = "aa20af7f68183a9c26f1901b4a6bd44dc94170bcd838ffe0715b67d59aab8c6817ea87";

const ADDRESS_PAY_TO_PUBKEY_MAINNET: &str = "vecno:qr36zdxs0dn3n0h799jhdl02qks5742lxjgmfsfj9xmlca7n4l6mw0s0n48nx";
const ADDRESS_PAY_TO_PUBKEY_ECDSA_MAINNET: &str = "vecno:qyp7xyqdshh6aylqct7x2je0pse4snep8glallgz8jppyaajz7y7qeq4x79fq4z";
const ADDRESS_PAY_TO_SCRIPTHASH_MAINNET: &str = "vecno:pzhh76qc82wzduvsrd9xh4zde9qhp0xc8rl7qu2mvl2e42uvdqt75zrcgpm00";

const ADDRESS_PAY_TO_PUBKEY_TESTNET: &str = "vecnotest:qr36zdxs0dn3n0h799jhdl02qks5742lxjgmfsfj9xmlca7n4l6mwwkfg6ezz";
const ADDRESS_PAY_TO_PUBKEY_ECDSA_TESTNET: &str = "vecnotest:qyp7xyqdshh6aylqct7x2je0pse4snep8glallgz8jppyaajz7y7qeq7jmc6p6h";
const ADDRESS_PAY_TO_SCRIPTHASH_TESTNET: &str = "vecnotest:pzhh76qc82wzduvsrd9xh4zde9qhp0xc8rl7qu2mvl2e42uvdqt75r97nw97t";

#[test]
fn creates_address_for_pay_to_pubkey() {
    let address = to_address("vecno", SCRIPT_PAY_TO_PUBKEY, 0).unwrap();
    assert_eq!(address, ADDRESS_PAY_TO_PUBKEY_MAINNET);
    let address = to_address("vecnotest", SCRIPT_PAY_TO_PUBKEY, 0).unwrap();
    assert_eq!(address, ADDRESS_PAY_TO_PUBKEY_TESTNET);
}

#[test]
fn creates_address_for_pay_to_pubkey_ecdsa() {
    let address = to_address("vecno", SCRIPT_PAY_TO_PUBKEY_ECDSA, 0).unwrap();
    assert_eq!(address, ADDRESS_PAY_TO_PUBKEY_ECDSA_MAINNET);
    let address = to_address("vecnotest", SCRIPT_PAY_TO_PUBKEY_ECDSA, 0).unwrap();
    assert_eq!(address, ADDRESS_PAY_TO_PUBKEY_ECDSA_TESTNET);
}

#[test]
fn creates_address_for_pay_to_scripthash() {
    let address = to_address("vecno", SCRIPT_PAY_TO_SCRIPTHASH, 0).unwrap();
    assert_eq!(address, ADDRESS_PAY_TO_SCRIPTHASH_MAINNET);
    let address = to_address("vecnotest", SCRIPT_PAY_TO_SCRIPTHASH, 0).unwrap();
    assert_eq!(address, ADDRESS_PAY_TO_SCRIPTHASH_TESTNET);
}

#[test]
fn creates_script_for_pay_to_pubkey() {
    let script = to_script(ADDRESS_PAY_TO_PUBKEY_MAINNET).unwrap();
    assert_eq!(script, SCRIPT_PAY_TO_PUBKEY);
    let script = to_script(ADDRESS_PAY_TO_PUBKEY_TESTNET).unwrap();
    assert_eq!(script, SCRIPT_PAY_TO_PUBKEY);
}

#[test]
fn creates_script_for_pay_to_pubkey_ecdsa() {
    let script = to_script(ADDRESS_PAY_TO_PUBKEY_ECDSA_MAINNET).unwrap();
    assert_eq!(script, SCRIPT_PAY_TO_PUBKEY_ECDSA);
    let script = to_script(ADDRESS_PAY_TO_PUBKEY_ECDSA_TESTNET).unwrap();
    assert_eq!(script, SCRIPT_PAY_TO_PUBKEY_ECDSA);
}

#[test]
fn creates_script_for_pay_to_scripthash() {
    let script = to_script(ADDRESS_PAY_TO_SCRIPTHASH_MAINNET).unwrap();
    assert_eq!(script, SCRIPT_PAY_TO_SCRIPTHASH);
    let script = to_script(ADDRESS_PAY_TO_SCRIPTHASH_TESTNET).unwrap();
    assert_eq!(script, SCRIPT_PAY_TO_SCRIPTHASH);
}
