# PrintBridge on TrueNAS 25.10: complete beginner setup

**Release status:** This is a prototype. The steps below take you from source
files to a TrueNAS Custom App, but nobody has yet tested this build with a
physical HL-2035, a TrueNAS host, Windows 11, or Android. Do not call it
production-ready before completing the physical checks below.

You need a Windows PC, a GitHub account, a TrueNAS 25.10 server with Apps
enabled, a USB printer, and an Android phone on your local Wi-Fi. GitHub builds
the image for you. You do not build an image on the NAS or buy a domain.

## Stage 1 — Put the source on GitHub

1. Download the project ZIP and use **Extract All** in Windows File Explorer.
   The extracted `printbridge` folder must contain `Dockerfile`, `app`, `docs`,
   and `.github`. Windows may hide the `.github` folder, but it must be present.
2. Download and install [GitHub Desktop](https://desktop.github.com/). Open it
   and sign in to your GitHub account.
3. Choose **File → Add local repository → Choose** and select the extracted
   `printbridge` folder (the one containing `Dockerfile`). The message
   **"This directory does not appear to be a Git repository"** is expected.
   Click the blue **create a repository** link in that message, **not** the
   **Add repository** button. In the next dialog, leave **Local path** as it
   is; choosing the same folder again can create an accidental nested folder.
   Click **Create repository**. Check that `Dockerfile` is still in the
   repository root, not inside a second `printbridge` folder.
4. Under **Changes**, check that `Dockerfile`, `app/web.py`, and
   `.github/workflows/image.yml` appear. Enter `First prototype` in **Summary**
   and click **Commit to main**.
5. Click **Publish repository**. Use the name `printbridge`, select your personal
   GitHub account, and clear **Keep this code private**. Click **Publish**.
   This publishes the source code. Do not take this step if you want the source
   to remain private; the guide's anonymous image download depends on a public
   package.
6. Open the repository in your browser. Verify that
   `.github/workflows/image.yml` is visible. If it is missing, the automated
   build cannot run; return to the extracted folder and commit the missing file.

**Checkpoint:** `https://github.com/YOUR_USERNAME/printbridge` shows the source.
Find `YOUR_USERNAME` at the top of your GitHub profile page.

## Stage 2 — Have GitHub build version v0.1.0

1. On your repository page, open **Releases → Create a new release** (or
   **Draft a new release**).
2. Click **Choose a tag**, enter `v0.1.0`, and select
   **Create new tag: v0.1.0** targeting `main`.
3. Title it `v0.1.0 prototype`, mark it as a **pre-release**, and click
   **Publish release**. This tag triggers **Build released image**.
4. Open **Actions → Build released image**. Wait until the job is green. It runs
   Python tests, then builds and publishes the image. If the job is red, do not
   install a guessed image: open the failed job and use its exact error when
   requesting a fix.
5. Open your GitHub profile → **Packages → printbridge → Package settings →
   Change package visibility → Public**, then confirm. A public GHCR package
   can be downloaded without registry credentials. A public repository does
   not necessarily make the separately published image public.

**Checkpoint:** the package lists `v0.1.0` and shows **Public**. Its image name
is `ghcr.io/your_username/printbridge:v0.1.0` with a lowercase username.

## Stage 3 — Install the TrueNAS Custom App

1. Note your NAS LAN IP from the TrueNAS browser address. For example, if you
   open `http://192.168.0.10/`, the IP is `192.168.0.10`.
2. Connect and power on the USB printer. Verify that the TrueNAS **Apps** page
   works. If TrueNAS asks for an Apps pool, select the pool used for your other
   apps and wait until initialization completes.
3. On the **same Windows PC** where you extracted the ZIP in Stage 1, open
   **File Explorer** (Windows key + E). Navigate to the extracted `printbridge`
   folder, the one that contains `Dockerfile`. Find
   `custom-app.yaml.template` in that folder. If file extensions are hidden,
   turn them on using **View → Show → File name extensions**.
4. Right-click `custom-app.yaml.template` → **Open with → Notepad**. If Notepad
   is not listed, choose **Choose another app → Notepad**. You are editing the
   copy on your Windows PC; there is no need to locate this file on TrueNAS.
5. In Notepad replace **only** the three values starting with `REPLACE`:

   - `REPLACE_GITHUB_USERNAME`: your lowercase GitHub username.
   - `REPLACE_WITH_LONG_LETTERS_AND_DIGITS_PASSWORD`: a unique password of at
     least 20 letters/digits. Save it in your password manager.
   - `REPLACE_WITH_TRUENAS_LAN_IP`: the LAN IP from step 1.

6. Press **Ctrl+S** to save. If Notepad offers **Save as**, choose **All files**
   as the file type and keep the exact name `custom-app.yaml.template` in the
   same folder. Press **Ctrl+A**, then **Ctrl+C** to copy all the YAML text.
7. Switch to the TrueNAS browser tab on the same Windows PC. Open
   **Apps → Discover → ⋮ → Install via YAML**. Set **Name** to
   `printbridge`, paste the YAML into the editor, and click **Save/Install**.
   TrueNAS downloads the prebuilt image from GHCR.
8. Wait for the app status to become **Running**. From Windows open
   `http://NAS-IP:8080/`, replacing `NAS-IP` with the actual address. Sign in
   as `admin` with the password from step 5. A YAML-installed Custom App may
   not show a Web UI button, so use the address directly.

**If installation fails:** Check that the image tag exists, the GHCR package is
Public, and your username is correct. If the app is Running but the site does
not open, TCP 8080 must be free on the NAS; TCP 631 must also be free for IPP.
This template uses `network_mode: host` so DNS-SD can reach the LAN. Changing
the YAML to remap ports does not work with host networking.

The password is stored in the app YAML, and prototype admin login uses HTTP
over the LAN. Never forward ports 8080 or 631 to the Internet or expose them
through a public reverse proxy. Use a password you do not use elsewhere.

## Stage 4 — Add the printer and test Windows 11

1. At `http://NAS-IP:8080/`, click **Add printer**.
2. **Search drivers** for `HL-2030`. Brother HL-2035 identifies itself over
   USB as `HL-2030 series`. Select **Brother HL-2030 series, brlaser** and
   verify the selection with a physical test page. This image builds the
   pinned upstream pdewacht/brlaser v6 release; it does not include Brother's
   proprietary driver.
3. Enter queue name `Brother_HL2035`, select the detected `usb://Brother/...`
   device, choose the matching driver, and click **Add printer**.
4. Return to **My printers**, click **Test page**, and confirm that paper
   physically comes out. A message that a job was sent is insufficient.
5. On Windows 11 go to **Settings → Bluetooth & devices → Printers & scanners
   → Add device → Add manually**. Choose the option to add a printer by name
   or address and enter `http://NAS-IP:631/printers/Brother_HL2035`.
6. Try the driver Windows offers first. Print a Windows test page and then a
   PDF containing accented characters. If the web UI's test page prints but
   Windows sends nothing, troubleshoot Windows/IPP separately.
7. To add a second printer later, click **Add printer** again and use a new
   queue name. The first queue is kept. Test both after restarting the app.

## Stage 5 — Test Android in two ways

1. Connect the phone to the same Wi-Fi/LAN as TrueNAS for the first test. Do
   not use a guest network that isolates clients.
2. Open `http://NAS-IP:8080/mobile` on the phone. Select the printer and a
   PDF, click **Print**, and confirm that the page physically comes out.
3. To test Android's **built-in Print menu**, on a Pixel open **Settings →
   Connected devices → Connection preferences → Printing** and enable the
   **Default Print Service**.
4. Open a PDF in an app that has **Print** in its menu. Select **Print** and
   look for `Brother_HL2035`. Select it and check physical output.
5. If it does not appear, install or enable **Mopria Print Service** from the
   Play Store and try again. Mopria also offers manual addition by IP; enter
   the NAS IP. This is a compatibility test, not a guarantee that Mopria will
   accept every legacy CUPS queue.

When `PRINTBRIDGE_ADVERTISE_IP` is set, the app makes experimental DNS-SD/mDNS
announcements for its queues. Discovery usually does not cross VLANs without
multicast forwarding. If `/mobile` prints but Android's Print menu does not,
native Android support is **not yet verified** for this setup; the PDF web
page remains available while the specific IPP/discovery problem is diagnosed.

## Restart, update, and resource check

- Reboot the NAS, verify the app is **Running**, and print again from Windows
  and Android. The template maps the USB bus rather than a device path whose
  number can change when a USB device is reconnected.
- The `config` and `spool` volumes preserve CUPS settings and pending jobs on
  container recreation. Back them up before changing image versions.
- After testing a new tag such as `v0.1.1`, edit the image tag in the app YAML,
  save, and test physical output. Keep the old version available for rollback.
- 512 MB RAM and 1 CPU are starting limits, **not measured minimums**. If large
  PDFs fail, raise RAM to 1 GB rather than accepting unreliable printing.
