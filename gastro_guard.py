import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt

# Initialize empty DataFrame
log_data = pd.DataFrame(columns=["Time", "Meal", "Pain Level", "Stress Level", "Remedy"])

# Function to submit data
def submit_data():
    global log_data
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    meal = meal_entry.get()
    pain = pain_scale.get()
    stress = stress_scale.get()
    remedy = remedy_entry.get()

    new_entry = {
        "Time": current_time,
        "Meal": meal,
        "Pain Level": pain,
        "Stress Level": stress,
        "Remedy": remedy
    }
    log_data = pd.concat([log_data, pd.DataFrame([new_entry])], ignore_index=True)  # updated for pandas 2.x
    status_label.config(text="Data logged successfully!")
    
    # Clear input fields after successful submission
    meal_entry.delete(0, tk.END)
    pain_scale.set(0)
    stress_scale.set(0)
    remedy_entry.delete(0, tk.END)

# Function to filter data based on time period
def filter_data_by_period(period):
    if log_data.empty:
        return pd.DataFrame()
    
    # Convert Time column to datetime if it isn't already
    data_copy = log_data.copy()
    data_copy["Time"] = pd.to_datetime(data_copy["Time"])
    
    # Calculate the cutoff date based on selected period
    now = datetime.now()
    if period == "week":
        cutoff_date = now - timedelta(days=7)
    elif period == "month":
        cutoff_date = now - timedelta(days=30)
    else:  # "all"
        return data_copy
    
    # Filter data
    filtered_data = data_copy[data_copy["Time"] >= cutoff_date]
    return filtered_data

# Function to show graph with filtering
def show_graph():
    if log_data.empty:
        status_label.config(text="No data to plot.")
        return
    
    # Get selected time period
    selected_period = time_filter.get()
    filtered_data = filter_data_by_period(selected_period)
    
    if filtered_data.empty:
        status_label.config(text=f"No data available for the selected {selected_period} period.")
        return
    
    # Create the plot
    plt.figure(figsize=(12, 6))
    plt.plot(filtered_data["Time"], filtered_data["Pain Level"], marker='o', label="Pain Level", linewidth=2)
    plt.plot(filtered_data["Time"], filtered_data["Stress Level"], marker='s', label="Stress Level", linewidth=2)
    
    # Customize the plot
    period_title = {"all": "All Time", "week": "Past Week", "month": "Past Month"}
    plt.title(f"Pain & Stress Levels Over Time - {period_title[selected_period]}")
    plt.ylabel("Level (0-10)")
    plt.xlabel("Time")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Update status
    status_label.config(text=f"Graph displayed for {period_title[selected_period].lower()} ({len(filtered_data)} entries)")
    plt.show()

# Function to show data summary
def show_summary():
    if log_data.empty:
        status_label.config(text="No data available for summary.")
        return
    
    selected_period = time_filter.get()
    filtered_data = filter_data_by_period(selected_period)
    
    if filtered_data.empty:
        status_label.config(text=f"No data available for the selected {selected_period} period.")
        return
    
    # Calculate summary statistics
    pain_avg = filtered_data["Pain Level"].mean()
    stress_avg = filtered_data["Stress Level"].mean()
    pain_max = filtered_data["Pain Level"].max()
    stress_max = filtered_data["Stress Level"].max()
    total_entries = len(filtered_data)
    
    period_title = {"all": "All Time", "week": "Past Week", "month": "Past Month"}
    
    summary_text = f"""
Summary for {period_title[selected_period]}:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Entries: {total_entries}
Average Pain Level: {pain_avg:.1f}/10
Average Stress Level: {stress_avg:.1f}/10
Max Pain Level: {pain_max}/10
Max Stress Level: {stress_max}/10
    """
    
    # Create summary window
    summary_window = tk.Toplevel(root)
    summary_window.title("Data Summary")
    summary_window.geometry("350x200")
    
    summary_label = tk.Label(summary_window, text=summary_text, justify="left", font=("Courier", 10))
    summary_label.pack(padx=20, pady=20)

# GUI layout
root = tk.Tk()
root.title("GastroGuard - Gastritis Assistant")
root.geometry("500x400")

# Create main frame
main_frame = ttk.Frame(root, padding="10")
main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

# Configure grid weights
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)
main_frame.columnconfigure(1, weight=1)

# Title
title_label = tk.Label(main_frame, text="GastroGuard - Gastritis Assistant", 
                      font=("Arial", 16, "bold"), fg="#2E7D32")
title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))

# Meal
tk.Label(main_frame, text="Meal/Food Consumed:", font=("Arial", 10)).grid(row=1, column=0, sticky="w", pady=5)
meal_entry = tk.Entry(main_frame, width=40, font=("Arial", 10))
meal_entry.grid(row=1, column=1, sticky="ew", pady=5)

# Pain Level
tk.Label(main_frame, text="Pain Level (0-10):", font=("Arial", 10)).grid(row=2, column=0, sticky="w", pady=5)
pain_scale = tk.Scale(main_frame, from_=0, to=10, orient="horizontal", font=("Arial", 10))
pain_scale.grid(row=2, column=1, sticky="ew", pady=5)

# Stress Level
tk.Label(main_frame, text="Stress Level (0-10):", font=("Arial", 10)).grid(row=3, column=0, sticky="w", pady=5)
stress_scale = tk.Scale(main_frame, from_=0, to=10, orient="horizontal", font=("Arial", 10))
stress_scale.grid(row=3, column=1, sticky="ew", pady=5)

# Remedy
tk.Label(main_frame, text="Remedy Used:", font=("Arial", 10)).grid(row=4, column=0, sticky="w", pady=5)
remedy_entry = tk.Entry(main_frame, width=40, font=("Arial", 10))
remedy_entry.grid(row=4, column=1, sticky="ew", pady=5)

# Submit button
submit_button = tk.Button(main_frame, text="Log Entry", command=submit_data, 
                         bg="#4CAF50", fg="white", font=("Arial", 10, "bold"))
submit_button.grid(row=5, column=0, columnspan=2, pady=15)

# Time filter section
filter_frame = ttk.LabelFrame(main_frame, text="Time Filter", padding="10")
filter_frame.grid(row=6, column=0, columnspan=2, sticky="ew", pady=10)
filter_frame.columnconfigure(1, weight=1)

tk.Label(filter_frame, text="View data for:", font=("Arial", 10)).grid(row=0, column=0, sticky="w")
time_filter = ttk.Combobox(filter_frame, values=["all", "week", "month"], state="readonly", font=("Arial", 10))
time_filter.set("all")  # Default selection
time_filter.grid(row=0, column=1, sticky="ew", padx=(10, 0))

# Action buttons frame
button_frame = ttk.Frame(main_frame)
button_frame.grid(row=7, column=0, columnspan=2, pady=15)

# Graph button
graph_button = tk.Button(button_frame, text="Show Graph", command=show_graph,
                        bg="#2196F3", fg="white", font=("Arial", 10, "bold"))
graph_button.pack(side="left", padx=(0, 10))

# Summary button
summary_button = tk.Button(button_frame, text="Show Summary", command=show_summary,
                          bg="#FF9800", fg="white", font=("Arial", 10, "bold"))
summary_button.pack(side="left")

# Status Label
status_label = tk.Label(main_frame, text="Welcome to GastroGuard! Start by logging your first entry.", 
                       fg="#2E7D32", font=("Arial", 10))
status_label.grid(row=8, column=0, columnspan=2, pady=10)

# Run GUI
root.mainloop()