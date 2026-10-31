# Things to ask

You talk to your AI app in plain words. It picks the right tool. Prompts in *italics*, grouped by job.

> [!TIP]
> If the app doesn't use the tools by itself, start with *"Use the Coolify-Cloudflare tools:"*.

## Look around

- *Give me an overview of my Coolify apps and anything that looks wrong.*
- *Show the last 50 log lines of the blog app.*
- *Why did the last deployment of the shop app fail?*
- *How much disk and memory is left on my server?* (needs the terminal)
- *List my DNS records and tell me which are proxied.*
- *Which hostnames does my tunnel send to which ports?*
- *Show the last actions this tool took or refused.*

## Change (you tap Confirm each time)

- *Restart the blog app.*
- *Deploy the shop app again without cache.*
- *Roll the shop app back to the previous image.*
- *Add a CNAME for test.example.com pointing to my tunnel.*
- *Turn on auto-deploy for the blog app.*

## Clean up

- *Clean up unused Docker images on my server.*
- *Run the nightly backup for the blog database now.*

## Undo

- *Roll the app back to the earlier image.*
- *Delete the test DNS record I just made.* (you also type the host name)

**What next:** [Every tool](tools.md) · [Safety](safety.md)
