const child = require('child_process');
const result = child.execSync('cd C:\\Users\\ASUS\\Documents\\AgnesCode\\checkin-xuqi && git show HEAD:gaming4free-renew/renew.py', {encoding: 'utf8'});
const lines = result.split('\n');
console.log('=== Lines 40-80 ===');
for (let i = 39; i < Math.min(80, lines.length); i++) {
    console.log((i+1).toString().padStart(4) + ':', lines[i].substring(0, 120));
}
console.log('\n=== Lines 100-140 ===');
for (let i = 99; i < Math.min(140, lines.length); i++) {
    console.log((i+1).toString().padStart(4) + ':', lines[i].substring(0, 120));
}
