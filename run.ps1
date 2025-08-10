# Send request and get chart_base64
$response = Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/" `
  -Method POST `
  -Form @{
      questions_file = Get-Item "questions.txt"
      file = Get-Item "data.csv"
      image = Get-Item "image.png"
  }

# Extract chart image from response
$base64 = $response.chart_base64 -replace '^data:image\/png;base64,', ''

# Save chart as PNG
$outputPath = "chart.png"
[IO.File]::WriteAllBytes($outputPath, [Convert]::FromBase64String($base64))

# Open the PNG file
Start-Process $outputPath

# Print answers
$response.answer | ForEach-Object { Write-Host $_ -ForegroundColor Green }
