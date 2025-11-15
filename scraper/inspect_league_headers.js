const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');

puppeteer.use(StealthPlugin());

(async () => {
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox'],
    timeout: 30000,
    protocolTimeout: 30000
  });

  const page = await browser.newPage();

  try {
    console.log('Inspecting league header structure for all sports...\n');

    const sports = [
      { name: 'football', url: 'https://www.flashscore.com/football/' },
      { name: 'basketball', url: 'https://www.flashscore.com/basketball/' },
      { name: 'tennis', url: 'https://www.flashscore.com/tennis/' },
      { name: 'hockey', url: 'https://www.flashscore.com/hockey/' }
    ];

    for (const sport of sports) {
      console.log('='.repeat(80));
      console.log('SPORT: ' + sport.name.toUpperCase());
      console.log('='.repeat(80));

      await page.goto(sport.url, { waitUntil: 'networkidle2', timeout: 30000 });
      await page.waitForSelector('.event__match', { timeout: 15000 });

      const results = await page.evaluate(() => {
        const matches = Array.from(document.querySelectorAll('.event__match')).slice(0, 10);

        const headerInfo = matches.map((match, idx) => {
          const prevSibling1 = match.previousElementSibling;
          const prevSibling2 = prevSibling1?.previousElementSibling;
          const prevSibling3 = prevSibling2?.previousElementSibling;

          return {
            matchNum: idx + 1,
            homeTeam: match.querySelector('.event__participant--home')?.textContent.trim(),
            prevSibling1: prevSibling1 ? { class: prevSibling1.className, text: prevSibling1.textContent.trim().substring(0, 80) } : 'NONE',
            prevSibling2: prevSibling2 ? { class: prevSibling2.className, text: prevSibling2.textContent.trim().substring(0, 80) } : 'NONE',
            prevSibling3: prevSibling3 ? { class: prevSibling3.className, text: prevSibling3.textContent.trim().substring(0, 80) } : 'NONE',
          };
        });

        return headerInfo;
      });

      results.forEach(r => {
        console.log('\nMatch ' + r.matchNum + ': ' + r.homeTeam);
        console.log('  Prev 1: [' + (r.prevSibling1.class || 'NONE') + '] "' + (r.prevSibling1.text || 'NONE').substring(0, 60) + '"');
        if (r.prevSibling2 !== 'NONE') {
          console.log('  Prev 2: [' + (r.prevSibling2.class || 'NONE') + '] "' + (r.prevSibling2.text || 'NONE').substring(0, 60) + '"');
        }
        if (r.prevSibling3 !== 'NONE') {
          console.log('  Prev 3: [' + (r.prevSibling3.class || 'NONE') + '] "' + (r.prevSibling3.text || 'NONE').substring(0, 60) + '"');
        }
      });

      console.log('\n');
    }

  } catch (error) {
    console.error('Error: ' + error.message);
  }

  await browser.close();
})();
