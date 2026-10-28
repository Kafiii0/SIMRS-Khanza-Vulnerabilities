# SIMRS Khanza Vulnerability Research & Disclosure

Security findings and proof of concept for SIMRS Khanza (mas-elkhanza/SIMRS-Khanza) through commit 36de12c. Coordinated disclosure report sent to vendor on October 16, 2026. CVE submission tracking: CAN-2026-2041057.

Finder: Kvii

## Summary

Two significant vulnerabilities were identified during independent testing:

1. Path Traversal (Zip Slip) in the auto-update client (KhanzaUpdater), allowing remote code execution or arbitrary file overwrite.
2. Unauthenticated Arbitrary File Deletion via hardcoded crypto keys and path-traversal URI bypass in the web application.

Full PDF writeup and audit breakdown is included in `POC_Security_Report_SIMRS_Khanza.pdf`.

## 1. Zip Slip (Path Traversal in KhanzaUpdater)

Target: `KhanzaUpdater/src/update/Main_Gui.java` (lines 206-214)  
CWE: CWE-22  
CVSS 4.0: `CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:A/VC:H/VI:H/VA:H/SC:H/SI:H/SA:H` (Score 9.4)

The updater pulls `dataupdate.zip` over plaintext HTTP and unpacks every entry directly by concatenating target folder with the zip entry name:

```java
(new File(root+entry.getName())).createNewFile();
```

Because `entry.getName()` isn't normalized or checked against the canonical root path, an entry like `../../critical_file.sys` escapes the update folder and overwrites files with the permissions of whichever user launched the updater.

Fix: Verify destination path canonical prefix before extraction.

```java
File destFile = new File(root, entry.getName());
if (!destFile.getCanonicalPath().startsWith(new File(root).getCanonicalPath())) {
    throw new SecurityException("Zip Slip Path Traversal Detected");
}
```

## 2. Unauthenticated Arbitrary File Deletion

Target: `webapps/berkasrawat/pages/detail.php` (lines 3 & 199)  
CWE: CWE-73, CWE-321

The delete action processes an encrypted token passed in `?iyem=`. The encryption key and IV (`Bar12345Bar12345` and `sayangsamakhanza`) are hardcoded in source code (`EnkripsiAES.java`). Anyone can craft a valid token specifying arbitrary file paths in `lokasi_file`. Furthermore, the URI check on line 3 can be bypassed using `pages/upload/../detail.php`, executing `unlink()` on any target file without an active session.

## Local PoC Verification

To verify both issues in an isolated sandbox, run:

```bash
python poc_cve.py
```

## Coordinated Disclosure Timeline

2026-10-16: Initial vulnerability report and PoC submitted to vendor maintainer via email.  
2026-10-28: CVE ID requested via MITRE CNA-LR (CAN-2026-2041057).
