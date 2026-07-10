# Data Exfiltration

The skill reads something sensitive — a secrets file, an environment
variable, a private key — and sends or exposes it somewhere it shouldn't
go, usually dressed up as a legitimate-sounding step ("double check the
values," "ship logs for analysis"). Real-world precedent: the 2021
Codecov Bash Uploader compromise shipped CI environment variables to an
attacker under the guise of normal telemetry upload.
