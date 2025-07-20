# Use the official AWS Lambda base image for Python 3.13
FROM public.ecr.aws/lambda/python:3.13

# Switch to root user to install system dependencies
USER root

# Use a build-time cache mount to provide a writable directory for the package manager.
# This is the modern, efficient way to handle package installation in constrained base images.
RUN dnf swap -y curl-minimal curl && \
    # Install all other required packages for headless Chrome.
    dnf install -y alsa-lib atk at-spi2-atk cups-libs dbus-libs expat fontconfig freetype glib2 gdk-pixbuf2 gtk3 liberation-sans-fonts libgcc libjpeg-turbo libpng libX11 libX11-xcb libxcb libXcomposite libXcursor libXdamage libXext libXfixes libXi libXrandr libXrender libXtst nspr nss pango pipewire-libs xorg-x11-fonts-75dpi xorg-x11-fonts-misc zlib jq unzip && \
    # Final cleanup to keep the image small.
    dnf clean all

# Download, unpack, and link the latest stable versions of Google Chrome and Chromedriver
# using the official "Chrome for Testing" JSON endpoints. This is the most reliable method.
RUN LATEST_JSON_URL="https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json" && \
    CHROME_URL=$(curl -s ${LATEST_JSON_URL} | jq -r '.channels.Stable.downloads.chrome[] | select(.platform=="linux64") | .url') && \
    DRIVER_URL=$(curl -s ${LATEST_JSON_URL} | jq -r '.channels.Stable.downloads.chromedriver[] | select(.platform=="linux64") | .url') && \
    \
    curl -s -L -o /tmp/chrome-linux64.zip ${CHROME_URL} && \
    unzip -q /tmp/chrome-linux64.zip -d /opt/ && \
    rm /tmp/chrome-linux64.zip && \
    \
    curl -s -L -o /tmp/chromedriver-linux64.zip ${DRIVER_URL} && \
    unzip -q /tmp/chromedriver-linux64.zip -d /opt/ && \
    rm /tmp/chromedriver-linux64.zip && \
    \
    ln -s /opt/chrome-linux64/chrome /usr/bin/google-chrome && \
    ln -s /opt/chromedriver-linux64/chromedriver /usr/bin/chromedriver

# Revert to the default non-root user for the Lambda runtime for security
# USER sbx_user1051

# Create a working directory
WORKDIR /var/task

# Copy requirements file first to leverage Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN python3 -m pip install -r requirements.txt

# Copy function code
COPY pmc_complaint_checker_v2.py repository.py ./

# Set the CMD to your handler.
# The format is <filename>.<handler_function>.
CMD [ "pmc_complaint_checker_v2.lambda_handler" ]