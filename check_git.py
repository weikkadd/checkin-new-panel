const child = require('child_process');
const result = child.execSync('cd C:\\Users\\ASUS\\Documents\\AgnesCode\\checkin-xuqi && git show HEAD:gaming4free-renew/renew.py', {encoding: 'utf8'});
const lines = result.split('\n');
console.log('Total lines:', lines.length);
console.log('Total bytes:', Buffer.byteLength(result, 'utf8'));
if (lines.length < 10) {
    console.log('FILE IS CORRUPTED IN GIT');
    console.log('Line 1 length:', lines[0].length);
    console.log('Line 1 starts:', JSON.stringify(lines[0].substring(0, 300)));
} else {
    console.log('File looks OK in git');
}
