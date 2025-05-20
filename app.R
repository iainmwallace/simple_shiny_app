# Load necessary libraries
library(shiny)
library(DT)
library(RSQLite)
library(DBI)
library(readr)
library(dplyr)

# Source modules
source("R/file_upload_module.R")
source("R/database_module.R")

# Define UI
ui <- shiny::fluidPage(
  shiny::titlePanel("CSV to SQLite Uploader"),
  shiny::sidebarLayout(
    shiny::sidebarPanel(
      fileUploadUI("upload_mod", "Step 1: Upload & Define Dataset"),
      shiny::hr(), # Add a horizontal line for separation
      shiny::actionButton("main_save_button", "Step 2: Save to Database", icon = shiny::icon("save"), class = "btn-primary")
    ),
    shiny::mainPanel(
      shiny::h4("Status:"),
      shiny::textOutput("status_message_out"),
      shiny::hr(), # Add a horizontal line for separation
    )
  )
)

# Define server logic
server <- function(input, output, session) {
  # Instantiate the file upload module
  upload_reactives <- shiny::callModule(fileUploadServer, "upload_mod")

  # Instantiate the database save module
  save_result_r <- shiny::callModule(
    databaseSaveServer,
    "db_mod",
    r_file_info = upload_reactives$file,
    r_dataset_name = upload_reactives$name,
    r_description = upload_reactives$description,
    r_raw_data = upload_reactives$data, 
    r_save_trigger = shiny::reactive(input$main_save_button)
  )

  # Observe the result from the database module to update the status message
  shiny::observeEvent(save_result_r(), {
    shiny::req(save_result_r()) 
    status_info <- save_result_r()

    shiny::showNotification(
      status_info$message,
      type = switch(status_info$type,
                    success = "message",
                    error = "error",
                    warning = "warning",
                    "default"), 
      duration = 5 
    )

    output$status_message_out <- shiny::renderText({
      paste(toupper(status_info$type), ":", status_info$message, "(Timestamp:", status_info$timestamp, ")")
    })
  })
}

# Run the application
shiny::shinyApp(ui, server)
