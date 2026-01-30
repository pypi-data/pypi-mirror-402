# VoidShred



VoidShred is a secure file shredding tool designed to permanently erase files beyond recovery. It uses multiple passes of random data overwriting, file corruption, and ephemeral cryptographic junk to maximize privacy. Perfect for sensitive files you want gone for good.



\## Features



\- Multi-level shredding (Levels 1-5)

&nbsp;   - \*\*Level 1:\*\* Basic 3-pass overwrite  

&nbsp;   - \*\*Level 2:\*\* 7-pass overwrite with size scrambling  

&nbsp;   - \*\*Level 3:\*\* 15-pass overwrite + cryptographic junk pass  

&nbsp;   - \*\*Level 4:\*\* 25-pass overwrite + file rename and metadata scrambling  

&nbsp;   - \*\*Level 5:\*\* 35-pass overwrite + maximum corruption, full flush to disk  

\- Supports any file type (.txt, .png, .jpg, .exe, etc.)  

\- Multi-pass random byte overwriting to prevent recovery  

\- Ephemeral cryptographic-style junk for extra security  

\- Fully CLI-based, lightweight, and cross-platform compatible  



\## Installation



```bash

pip install voidshred

````



\## Usage



```bash

voidshred <file\_path> --level <level\_number>

```



\* `<file\_path>`: Path to the file you want to permanently delete

\* `<level\_number>`: Shred intensity from 1 (basic) to 5 (maximum security)



\*\*Example:\*\*



```bash

voidshred "C:\\Users\\Username\\Documents\\secret\_file.txt" --level 5

```



This will shred `secret\_file.txt` with the maximum security level.



\## Warning



\* \*\*Irreversible:\*\* Once shredded, files cannot be recovered

\* Recommended to test on dummy files first

\* SSD users: due to wear leveling, complete destruction is not guaranteed; use full-disk encryption for sensitive data

