export const formatRWF = (amount, showSymbol = true) => {
  const numericAmount = parseFloat(amount) || 0;
  const formatted = numericAmount.toLocaleString("en-RW", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  });

  return showSymbol ? `RWF ${formatted}` : formatted;
};

export const formatRWFCompact = (amount) => {
  const numericAmount = parseFloat(amount) || 0;

  // For amounts over 1 million, show in millions
  if (numericAmount >= 1000000) {
    return `RWF ${(numericAmount / 1000000).toFixed(1)}M`;
  }

  // For amounts over 1000, show in thousands
  if (numericAmount >= 1000) {
    return `RWF ${(numericAmount / 1000).toFixed(1)}K`;
  }

  return formatRWF(amount);
};

export const parseCurrency = (currencyString) => {
  if (!currencyString) return 0;
  const cleaned = currencyString
    .toString()
    .replace(/RWF\s?/gi, "")
    .replace(/,/g, "");
  return parseFloat(cleaned) || 0;
};

export const isValidCurrency = (amount) => {
  const numericAmount = parseFloat(amount);
  return !isNaN(numericAmount) && numericAmount >= 0;
};
