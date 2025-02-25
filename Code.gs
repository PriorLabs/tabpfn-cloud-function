// Configuration
const CLOUD_FUNCTION_URL = 'https://your-region-your-project.cloudfunctions.net/infer-category';
const N_FEATURES = 16; // 6 base features + 10 text embeddings
const N_ESTIMATORS = 8; // Number of forward passes in TabPFN
const MAX_CELLS_PER_REQUEST = 100000; // API size limitation
const BATCH_SIZE = Math.min(100, Math.floor(MAX_CELLS_PER_REQUEST / (N_FEATURES * N_ESTIMATORS))); // Optimal batch size

// Add menu to the spreadsheet
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('Transaction Categories')
    .addItem('Predict Categories', 'predictCategories')
    .addItem('Show API Usage', 'showAPIUsage')
    .addToUi();
}

// Main function to predict categories
function predictCategories() {
  const ui = SpreadsheetApp.getUi();
  const sheet = SpreadsheetApp.getActiveSheet();
  
  try {
    // 1. Get and validate sheet data
    const { transactions, columns } = getSheetData(sheet);
    if (transactions.length === 0) {
      ui.alert('No transactions found', 'Please make sure you have data in the sheet with required columns: dateOp, transaction_description, amount', ui.ButtonSet.OK);
      return;
    }
    
    // 2. Process in batches
    let totalProcessed = 0;
    let totalErrors = 0;
    
    // Process each batch
    for (let i = 0; i < transactions.length; i += BATCH_SIZE) {
      const batch = transactions.slice(i, Math.min(i + BATCH_SIZE, transactions.length));
      const results = processBatch(batch);
      
      if (results) {
        // Write results to sheet
        writeResults(sheet, results, columns);
        totalProcessed += results.processed;
        totalErrors += results.errors;
      }
    }
    
    // 3. Clear existing predictions and apply formatting
    clearExistingPredictions(sheet, columns);
    applyFormatting(sheet, columns);
    
    // 4. Show summary
    ui.alert(
      'Processing Complete',
      `Total transactions: ${transactions.length}\n` +
      `Successfully processed: ${totalProcessed}\n` +
      `Errors: ${totalErrors}\n\n` +
      `Batch size used: ${BATCH_SIZE} transactions`,
      ui.ButtonSet.OK
    );
    
  } catch (error) {
    ui.alert('Error', `Failed to process transactions: ${error.toString()}`, ui.ButtonSet.OK);
    console.error('Error in predictCategories:', error);
  }
}

// Get and validate sheet data
function getSheetData(sheet) {
  const dataRange = sheet.getDataRange();
  const values = dataRange.getValues();
  const headers = values[0];
  
  // Get column indices
  const columns = {
    dateCol: headers.indexOf('dateOp'),
    descCol: headers.indexOf('transaction_description'),
    amountCol: headers.indexOf('amount'),
    categoryCol: headers.indexOf('predicted_category'),
    confidenceCol: headers.indexOf('confidence'),
    errorCol: headers.indexOf('error')
  };
  
  // Validate required columns
  if (columns.dateCol === -1 || columns.descCol === -1 || columns.amountCol === -1) {
    throw new Error('Required columns not found: dateOp, transaction_description, amount');
  }
  
  // Add prediction columns if they don't exist
  if (columns.categoryCol === -1) {
    columns.categoryCol = headers.length;
    sheet.getRange(1, columns.categoryCol + 1).setValue('predicted_category');
  }
  if (columns.confidenceCol === -1) {
    columns.confidenceCol = columns.categoryCol + 1;
    sheet.getRange(1, columns.confidenceCol + 1).setValue('confidence');
  }
  if (columns.errorCol === -1) {
    columns.errorCol = columns.confidenceCol + 1;
    sheet.getRange(1, columns.errorCol + 1).setValue('error');
  }
  
  // Prepare transactions data
  const transactions = [];
  for (let i = 1; i < values.length; i++) {
    const row = values[i];
    if (!row[columns.descCol]) continue;
    
    // Convert date to ISO format
    let date = row[columns.dateCol];
    if (!(date instanceof Date)) {
      try {
        date = new Date(date);
      } catch (e) {
        console.error('Error parsing date:', e);
        continue;
      }
    }
    
    // Convert amount to number
    let amount = row[columns.amountCol];
    if (typeof amount === 'string') {
      amount = parseFloat(amount.replace(',', '.'));
    }
    
    transactions.push({
      id: i,
      dateOp: date.toISOString(),
      transaction_description: String(row[columns.descCol]),
      amount: Number(amount)
    });
  }
  
  return { transactions, columns };
}

// Process a batch of transactions
function processBatch(transactions) {
  try {
    // Prepare request payload
    const payload = JSON.stringify({ transactions: transactions });
    
    // Call cloud function
    const response = UrlFetchApp.fetch(CLOUD_FUNCTION_URL, {
      method: 'post',
      contentType: 'application/json',
      payload: payload,
      muteHttpExceptions: true
    });
    
    // Get response text and save it to JSON sheet
    const responseText = response.getContentText();
    saveJsonResponse(payload, responseText);
    
    // Parse response
    const responseData = JSON.parse(responseText);
    
    // Handle errors
    if (responseData.error) {
      console.error('API Error:', responseData);
      return {
        processed: 0,
        errors: transactions.length,
        errorMessage: responseData.message || 'Unknown API error',
        results: [],
        errorMap: new Map(transactions.map(t => [t.id.toString(), { error: responseData.message }]))
      };
    }
    
    // Process results
    const resultMap = new Map();
    const errorMap = new Map();
    
    if (Array.isArray(responseData.results)) {
      responseData.results.forEach(result => {
        resultMap.set(result.transaction_id.toString(), result);
      });
    }
    
    if (Array.isArray(responseData.errors)) {
      responseData.errors.forEach(error => {
        errorMap.set(error.transaction_id.toString(), error);
      });
    }
    
    return {
      processed: responseData.total_processed || 0,
      errors: responseData.total_errors || 0,
      results: resultMap,
      errorMap: errorMap
    };
    
  } catch (error) {
    console.error('Error processing batch:', error);
    return {
      processed: 0,
      errors: transactions.length,
      errorMessage: error.toString(),
      results: [],
      errorMap: new Map(transactions.map(t => [t.id.toString(), { error: error.toString() }]))
    };
  }
}

// Save JSON request and response to a separate sheet
function saveJsonResponse(requestPayload, responseText) {
  // Get or create JSON sheet
  let jsonSheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('JSON');
  if (!jsonSheet) {
    jsonSheet = SpreadsheetApp.getActiveSpreadsheet().insertSheet('JSON');
  }
  
  // Clear existing content
  jsonSheet.clear();
  
  // Format JSON for better readability
  const formattedRequest = JSON.stringify(JSON.parse(requestPayload), null, 2);
  const formattedResponse = JSON.stringify(JSON.parse(responseText), null, 2);
  
  // Write to sheet
  jsonSheet.getRange('A1').setValue('Request Payload:');
  jsonSheet.getRange('A2').setValue(formattedRequest);
  jsonSheet.getRange('A4').setValue('Response:');
  jsonSheet.getRange('A5').setValue(formattedResponse);
  
  // Format cells
  jsonSheet.getRange('A1:A4').setFontWeight('bold');
  jsonSheet.autoResizeColumn(1);
}

// Write results to sheet
function writeResults(sheet, results, columns) {
  results.results.forEach((result, transactionId) => {
    const row = parseInt(transactionId) + 1;
    sheet.getRange(row, columns.categoryCol + 1).setValue(result.predicted_category);
    sheet.getRange(row, columns.confidenceCol + 1).setValue(result.confidence);
    sheet.getRange(row, columns.errorCol + 1).setValue('');
  });
  
  results.errorMap.forEach((error, transactionId) => {
    const row = parseInt(transactionId) + 1;
    sheet.getRange(row, columns.categoryCol + 1).setValue('');
    sheet.getRange(row, columns.confidenceCol + 1).setValue('');
    sheet.getRange(row, columns.errorCol + 1).setValue(error.error || error.message || 'Unknown error');
  });
}

// Clear existing predictions
function clearExistingPredictions(sheet, columns) {
  const numRows = sheet.getLastRow() - 1;
  if (numRows > 0) {
    sheet.getRange(2, columns.categoryCol + 1, numRows, 1).clearContent();
    sheet.getRange(2, columns.confidenceCol + 1, numRows, 1).clearContent();
    sheet.getRange(2, columns.errorCol + 1, numRows, 1).clearContent();
  }
}

// Apply conditional formatting
function applyFormatting(sheet, columns) {
  // Clear existing rules
  sheet.clearConditionalFormatRules();
  const rules = [];
  
  // Get ranges
  const lastRow = sheet.getLastRow();
  const confidenceRange = sheet.getRange(2, columns.confidenceCol + 1, lastRow - 1, 1);
  const errorRange = sheet.getRange(2, columns.errorCol + 1, lastRow - 1, 1);
  
  // Confidence formatting
  rules.push(SpreadsheetApp.newConditionalFormatRule()
    .whenNumberGreaterThanOrEqualTo(0.8)
    .setBackground('#b7e1cd')  // Light green
    .setBold(true)
    .setRanges([confidenceRange])
    .build());
    
  rules.push(SpreadsheetApp.newConditionalFormatRule()
    .whenNumberBetween(0.5, 0.8)
    .setBackground('#fce8b2')  // Light yellow
    .setRanges([confidenceRange])
    .build());
    
  rules.push(SpreadsheetApp.newConditionalFormatRule()
    .whenNumberLessThan(0.5)
    .setBackground('#f4c7c3')  // Light red
    .setRanges([confidenceRange])
    .build());
  
  // Error formatting
  rules.push(SpreadsheetApp.newConditionalFormatRule()
    .whenCellNotEmpty()
    .setBackground('#ea4335')  // Error red
    .setFontColor('#ffffff')   // White text
    .setRanges([errorRange])
    .build());
  
  sheet.setConditionalFormatRules(rules);
}

// Check API status and limits
function checkAPIStatus() {
  try {
    const response = UrlFetchApp.fetch(CLOUD_FUNCTION_URL, {
      method: 'post',
      contentType: 'application/json',
      payload: JSON.stringify({ 
        transactions: [{
          id: 1,
          dateOp: new Date().toISOString(),
          transaction_description: "test",
          amount: 0
        }] 
      }),
      muteHttpExceptions: true
    });
    
    const headers = response.getAllHeaders();
    
    // Set reset time to midnight UTC
    const resetTime = new Date();
    resetTime.setUTCHours(24, 0, 0, 0);  // This will set it to next day midnight UTC
    
    return {
      limit: parseInt(headers['X-RateLimit-Limit'] || '5000000'),
      remaining: parseInt(headers['X-RateLimit-Remaining'] || '0'),
      resetTime: resetTime
    };
  } catch (error) {
    console.error('Error checking API status:', error);
    return null;
  }
}

// Check if we can process the requested number of transactions
function checkAPILimit(numTransactions, apiUsage) {
  const ui = SpreadsheetApp.getUi();
  const cellsNeeded = numTransactions * N_FEATURES * N_ESTIMATORS;
  
  if (cellsNeeded > apiUsage.remaining) {
    const remainingTransactions = Math.floor(apiUsage.remaining / (N_FEATURES * N_ESTIMATORS));
    const resetTime = apiUsage.resetTime.toLocaleString('en-US', { 
      dateStyle: 'medium', 
      timeStyle: 'medium',
      timeZone: 'UTC'
    });
    
    ui.alert(
      'API Limit Warning',
      `Not enough capacity to process ${numTransactions} transactions.\n\n` +
      `Available capacity: ${remainingTransactions} transactions\n` +
      `API limit will reset at: ${resetTime} UTC\n\n` +
      (remainingTransactions > 0 ? 'Would you like to process the available transactions?' : 'Please try again after the limit resets.'),
      remainingTransactions > 0 ? ui.ButtonSet.YES_NO : ui.ButtonSet.OK
    );
    
    if (remainingTransactions > 0) {
      return ui.getResponseText() === 'YES';
    }
    return false;
  }
  return true;
}

// Show current API usage
function showAPIUsage() {
  const ui = SpreadsheetApp.getUi();
  const usage = checkAPIStatus();
  
  if (!usage) {
    ui.alert('Error', 'Unable to fetch API usage information', ui.ButtonSet.OK);
    return;
  }
  
  const usagePercent = ((usage.limit - usage.remaining) / usage.limit * 100).toFixed(1);
  const estimatedTransactions = Math.floor(usage.remaining / (N_FEATURES * N_ESTIMATORS));
  const resetTime = usage.resetTime.toLocaleString('en-US', { 
    dateStyle: 'medium', 
    timeStyle: 'medium',
    timeZone: 'UTC'
  });
  
  ui.alert(
    'API Usage Status',
    `Current Usage: ${(usage.limit - usage.remaining).toLocaleString()} / ${usage.limit.toLocaleString()} cells (${usagePercent}%)\n\n` +
    `Remaining Capacity:\n` +
    `- ${usage.remaining.toLocaleString()} cells\n` +
    `- Approximately ${estimatedTransactions.toLocaleString()} predictions\n\n` +
    `Batch Information:\n` +
    `- Maximum batch size: ${BATCH_SIZE} transactions\n` +
    `- Cost per prediction: ${(N_FEATURES * N_ESTIMATORS).toLocaleString()} cells\n\n` +
    `Limit Reset Time: ${resetTime} UTC`,
    ui.ButtonSet.OK
  );
} 