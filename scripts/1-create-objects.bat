az group create -l northeurope -n e2e_covid
az storage account create -l northeurope -n e2estore -g e2e_covid --sku Standard_LRS