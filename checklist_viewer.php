<?php
// Ścieżka do pliku JSON (wrzuć go np. do tego samego folderu co ten plik PHP)
$jsonFile = __DIR__ . "/delante.pl_2025-08-22_15-02.json";

// Wczytanie pliku
if (!file_exists($jsonFile)) {
    die("Brak pliku JSON: $jsonFile");
}

$json = file_get_contents($jsonFile);
$data = json_decode($json, true);

if (!$data) {
    die("Błąd dekodowania JSON");
}
?>
<!DOCTYPE html>
<html lang="pl">
<head>
  <meta charset="UTF-8">
  <title>Raport SEO</title>
  <style>
    body { font-family: Arial, sans-serif; background: #f9f9f9; margin: 20px; }
    h1 { text-align: center; }
    .check {
      background: #fff; margin: 15px 0; padding: 15px; border-radius: 8px;
      box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .status { font-weight: bold; padding: 4px 8px; border-radius: 5px; }
    .PASS { background: #d4edda; color: #155724; }
    .FAIL { background: #f8d7da; color: #721c24; }
    .WARN { background: #fff3cd; color: #856404; }
    .ERROR { background: #f5c6cb; color: #721c24; }
    pre { background: #f0f0f0; padding: 10px; border-radius: 5px; overflow-x: auto; }
  </style>
</head>
<body>
  <h1>Raport SEO</h1>

  <?php foreach ($data as $check): ?>
    <div class="check">
      <h2><?= htmlspecialchars($check['name']) ?></h2>
      <p>Status: <span class="status <?= htmlspecialchars($check['status']) ?>">
        <?= htmlspecialchars($check['status']) ?>
      </span></p>

      <?php if (!empty($check['metrics'])): ?>
        <h3>Metryki:</h3>
        <pre><?= htmlspecialchars(json_encode($check['metrics'], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE)) ?></pre>
      <?php endif; ?>

      <?php if (!empty($check['samples'])): ?>
        <h3>Przykłady:</h3>
        <pre><?= htmlspecialchars(json_encode($check['samples'], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE)) ?></pre>
      <?php endif; ?>

      <?php if (!empty($check['fix_hint'])): ?>
        <h3>Rekomendacja:</h3>
        <p><?= htmlspecialchars($check['fix_hint']) ?></p>
      <?php endif; ?>
    </div>
  <?php endforeach; ?>

</body>
</html>
