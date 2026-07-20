const child = require('child_process');
const result = child.execSync('cd C:\\Users\\ASUS\\Documents\\AgnesCode\\checkin-xuqi && git show HEAD:gaming4free-renew/renew.py', {encoding: 'utf8'});
const lines = result.split('\n');
console.log('Lines:', lines.length, 'Bytes:', Buffer.byteLength(result, 'utf8'));
if (lines.length < 10) {
    console.log('CORRUPTED IN GIT');
    console.log('L1 len:', lines[0].length);
} else {
    console.log('OK in git');
    for (let i = 35; i < Math.min(50, lines.length); i++) {
        console.log((i+1).toString().padStart(4) + ':', lines[i].substring(0, 120));
    }
}
