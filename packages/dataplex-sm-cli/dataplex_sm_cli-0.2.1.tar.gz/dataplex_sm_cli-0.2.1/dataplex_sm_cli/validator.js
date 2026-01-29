const fs = require('fs');
const yaml = require('js-yaml');

/**
 * YAML Validator - validates YAML files for syntax and structure
 * Usage: node validator.js <file_path>
 */

const filePath = process.argv[2];

if (!filePath) {
  console.log(JSON.stringify({
    success: false,
    error: "File path is required"
  }));
  process.exit(1);
}

try {
  const fileContent = fs.readFileSync(filePath, 'utf8');
  const data = yaml.load(fileContent);
  
  console.log(JSON.stringify({
    success: true,
    message: "YAML is valid",
    data: data
  }));
  process.exit(0);
} catch (error) {
  console.log(JSON.stringify({
    success: false,
    error: error.message,
    line: error.mark?.line,
    column: error.mark?.column
  }));
  process.exit(1);
}
