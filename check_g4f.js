const child = require('child_process');
const result = child.execSync('cd C:\\Users\\ASUS\\Documents\\AgnesCode\\checkin-xuqi && git show HEAD:gaming4free-renew/renew.py', {encoding: 'utf8'});
const lines = result.split('\n');
console.log('Total lines:', lines.length);
console.log('Size bytes:', Buffer.byteLength(result, 'utf8'));
if (lines.length < 10) {
    console.log('FILE CORRUPTED IN GIT');
    console.log('Line1:', JSON.stringify(lines[0].substring(0, 200)));
} else {
    console.log('OK - file has', lines.length, 'lines');
    for (let i = 0; i < Math.min(45, lines.length); i++) {
        console.log((i+1).toString().padStart(4) + ':', lines[i].substring(0, 120));
    }
}
