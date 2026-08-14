# Build image for tools/build.py: TeX Live + Node (mermaid-cli) + Chromium.
#
# Built and pushed to ghcr.io by .github/workflows/image.yml, which only fires
# when this file changes. The document workflow then pulls a warm image instead
# of installing TeX Live on every push.
FROM texlive/texlive:latest

RUN apt-get update && apt-get install -y --no-install-recommends \
        nodejs npm chromium python3 \
    && rm -rf /var/lib/apt/lists/*

# mermaid-cli drives puppeteer; point it at the chromium we just installed
# instead of letting it download a second browser at render time.
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium \
    PUPPETEER_SKIP_DOWNLOAD=true

# Bake mermaid-cli in so `npx -y` resolves it offline rather than hitting the
# registry on every diagram.
RUN npm install -g @mermaid-js/mermaid-cli

WORKDIR /work
