# TOPSIS Python Package

This package implements the **TOPSIS (Technique for Order Preference by Similarity to Ideal Solution)** method for solving Multi-Criteria Decision Making (MCDM) problems.

---

## 📦 Installation

```bash
pip install Topsis-Saniya-102303183
```

---

## 🚀 Usage

Run the package using the command line as follows:

```bash
topsis <InputDataFile.csv> <Weights> <Impacts> <ResultFile.csv>
```

---

## 📌 Parameters

- **InputDataFile.csv**  
  CSV file containing alternatives and criteria values.

- **Weights**  
  Comma-separated numerical weights  
  Example: `1,1,1,1`

- **Impacts**  
  Comma-separated impacts  
  `+` for benefit, `-` for cost  
  Example: `+,-,+,+`

- **ResultFile.csv**  
  Output CSV file with TOPSIS score and rank.

---

## 📄 Example

### Sample Input File (`sample.csv`)

```
Model,Storage,Camera,Price,Looks
M1,16,12,250,5
M2,16,8,200,3
M3,32,16,300,4
M4,32,8,275,4
M5,16,16,225,2
```

### Command

```bash
topsis sample.csv "1,1,1,1" "+,-,+,+" result.csv
```

---

## 📊 Output

The output CSV file will contain:
- **Topsis Score**
- **Rank**

Higher score indicates a better alternative.

---

## ⚠️ Assumptions

- Input file must be a CSV file
- All values must be numeric
- Number of weights must equal number of criteria
- Impacts must be either `+` or `-`
- No missing values allowed

---

## 👩‍💻 Author
Saniya

---

## 📜 License
MIT License
