# OpenBMC 工具的基本指令和功能 {#p10hai_openbmc_basecommands__title__1 .topictitle1}

OpenBMC
工具支援使用系統事件日誌、更新系統韌體、識別系統、關閉系統電源，以及其他服務相關功能。

## OpenBMC 工具最上層選項 {#task_a2l_nw2_sdb__title__1 .topictitle2}

::::: {.body .taskbody}
進一步瞭解 OpenBMC 工具指令的最上層選項。

:::: {.section .section .context role="region" aria-label="OpenBMC 工具最上層選項: 關於此作業"}
::: tasklabel
### 關於此作業 {#tasktask_a2l_nw2_sdb__context__1 .sectiontitle .tasklabel}
:::

- [-H]{.kbd .ph .userinput}：BMC 的主機名稱或 IP 位址。
- [-U]{.kbd .ph .userinput}：用來登入的使用者名稱。
- [-A]{.kbd .ph .userinput}：提供要求密碼的提示。
- [-P]{.kbd .ph .userinput}：使用者名稱的密碼。
- [-j]{.kbd .ph .userinput}：將輸出格式變更為 JSON。
- [-t]{.kbd .ph .userinput}：要使用之原則表格的位置。
- [-T]{.kbd .ph .userinput}：提供登入、執行指令及登出的時間統計資料。
- [-V]{.kbd .ph .userinput}：顯示 OpenBMC 工具的現行版本。
::::
:::::

## 系統事件日誌指令 {#task_ug5_qby_fcb__title__1 .topictitle2}

:::: {.body .taskbody}
進一步瞭解 OpenBMC 工具的系統事件日誌指令。

::: tasklabel
### 程序 {#tasktask_ug5_qby_fcb__steps-unordered__1 .sectiontitle .tasklabel}
:::

- [若要以可讀取的格式列印系統事件日誌清單，請使用下列指令： ]{.cmd}

  ::: {.itemgroup .info}
  [openbmctool -U \<username\> -P \<password\> -H \<BMC IP address or
  BMC host name\> sel print]{.kbd .ph .userinput}
  :::
- [若要列出原始資料中的系統事件日誌，請使用下列指令： ]{.cmd}

  ::: {.itemgroup .info}
  [openbmctool -U \<username\> -P \<password\> -H \<BMC IP address or
  BMC host name\> sel list]{.kbd .ph .userinput}
  :::
- [若要將系統事件日誌的狀態變更為已解決，請使用下列指令：]{.cmd}

  ::: {.itemgroup .info}
  [openbmctool -U \<username\> -P \<password\> -H \<BMC IP address or
  BMC host name\> sel resolve -n x]{.kbd .ph .userinput}，其中 *x*
  是系統事件日誌號碼。
  :::
- [若要收集所有服務資料（包括系統事件日誌），請使用下列指令：]{.cmd}

  ::: {.itemgroup .info}
  [openbmctool -U \<username\> -P \<password\> -H \<BMC IP address or
  BMC host name\> collect_service_data]{.kbd .ph .userinput}.
  :::
- [若要清除 gard 記錄以停用硬體，請使用下列指令： ]{.cmd}

  ::: {.itemgroup .info}
  [openbmctool -U \<username\> -P \<password\> -H \<BMC IP address or
  BMC host name\> gardclear]{.kbd .ph .userinput}
  :::
- [若要清除項目的警示日誌，請使用下列指令： ]{.cmd}

  ::: {.itemgroup .info}
  [openbmctool -U \<username\> -P \<password\> -H \<BMC IP address or
  BMC host name\> sel clear]{.kbd .ph .userinput}
  :::
::::

## 系統韌體更新指令 {#task_g24_dcy_fcb__title__1 .topictitle2}

:::: {.body .taskbody}
進一步瞭解系統韌體更新指令。

::: tasklabel
### 程序 {#tasktask_g24_dcy_fcb__steps-unordered__1 .sectiontitle .tasklabel}
:::

- [若要更新系統韌體，請使用下列指令： ]{.cmd}

  ::::: {.itemgroup .info}
  :::: p
  [openbmctool -U \<username\> -P \<password\> -H \<BMC IP address or
  BMC host name\> firmware flash \<bmc or pnor\> -f xxx.tar]{.kbd .ph
  .userinput}，其中 *bmc* 或 *pnor* 是您要向系統閃動的映像檔類型。

  ::: note
  [附註:]{.notetitle} 如果您與 TAR
  檔不在相同的資料夾中，則必須包括檔案所在資料夾的完整路徑。
  :::
  ::::
  :::::
- [若要啟動 BMC 中可用的韌體映像檔，請使用下列指令： ]{.cmd}

  ::: {.itemgroup .info}
  [openbmctool -U \<username\> -P \<password\> -H \<BMC IP address or
  BMC host name\> firmware activate \<firmware image ID\>]{.kbd .ph
  .userinput}
  :::
::::

## 系統識別指令 {#task_jfd_jcy_fcb__title__1 .topictitle2}

:::: {.body .taskbody}
進一步瞭解系統識別指令。

::: tasklabel
### 程序 {#tasktask_jfd_jcy_fcb__steps-unordered__1 .sectiontitle .tasklabel}
:::

- [若要啟動藍色系統識別 LED，請使用下列指令： ]{.cmd}

  ::: {.itemgroup .info}
  [openbmctool -U \<username\> -P \<password\> -H \<BMC IP address or
  BMC host name\> chassis identify on]{.kbd .ph .userinput}
  :::
- [若要關閉藍色系統識別 LED，請使用下列指令：]{.cmd}

  ::: {.itemgroup .info}
  [openbmctool -U \<username\> -P \<password\> -H \<BMC IP address or
  BMC host name\> chassis identify off]{.kbd .ph .userinput}
  :::
- [若要檢查藍色系統識別 LED 的狀態，請使用下列指令：]{.cmd}

  ::: {.itemgroup .info}
  [openbmctool -U \<username\> -P \<password\> -H \<BMC IP address or
  BMC host name\> chassis identify status]{.kbd .ph .userinput}
  :::
::::

## 系統開啟電源及關閉電源指令 {#task_fd3_3nf_gcb__title__1 .topictitle2}

:::: {.body .taskbody}
進一步瞭解系統電源開啟和關閉指令。

::: tasklabel
### 程序 {#tasktask_fd3_3nf_gcb__steps-unordered__1 .sectiontitle .tasklabel}
:::

- [若要檢查系統的電源狀態，請使用下列指令：]{.cmd}

  ::: {.itemgroup .info}
  [openbmctool -U \<username\> -P \<password\> -H \<BMC IP address or
  BMC host name\> chassis power status]{.kbd .ph .userinput}
  :::
- [若要開啟系統電源，請使用下列指令： ]{.cmd}

  ::: {.itemgroup .info}
  [openbmctool -U \<username\> -P \<password\> -H \<BMC IP address or
  BMC host name\> chassis power on]{.kbd .ph .userinput}
  :::
- [若要正常關閉系統電源，請使用下列指令：]{.cmd}

  ::: {.itemgroup .info}
  [openbmctool -U \<username\> -P \<password\> -H \<BMC IP address or
  BMC host name\> chassis power softoff]{.kbd .ph .userinput}
  :::
- [若要立即關閉系統電源，請使用下列指令： ]{.cmd}

  ::: {.itemgroup .info}
  [openbmctool -U \<username\> -P \<password\> -H \<BMC IP address or
  BMC host name\> chassis power hardoff]{.kbd .ph .userinput}
  :::
::::

## 系統感應器指令 {#task_yy3_2c2_sdb__title__1 .topictitle2}

:::::: {.body .taskbody}
進一步瞭解系統感應器指令。

::: tasklabel
### 程序 {#tasktask_yy3_2c2_sdb__steps-unordered__1 .sectiontitle .tasklabel}
:::

:::: {.step .p}
[若要顯示所有監視感應器的清單，請使用下列指令： ]{.cmd}

::: {.itemgroup .info}
[openbmctool -U \<username\> -P \<password\> -H \<BMC IP address or BMC
host name\> sensors print]{.kbd .ph .userinput}

或

[openbmctool -U \<username\> -P \<password\> -H \<BMC IP address or BMC
host name\> sensors list]{.kbd .ph .userinput}
:::
::::
::::::

## 系統 FRU 指令 {#task_at3_5c2_sdb__title__1 .topictitle2}

:::: {.body .taskbody}
進一步瞭解系統 FRU 指令。

::: tasklabel
### 程序 {#tasktask_at3_5c2_sdb__steps-unordered__1 .sectiontitle .tasklabel}
:::

- [如果要顯示所有庫存項目的清單，請使用下列指令： ]{.cmd}

  ::: {.itemgroup .info}
  [openbmctool -U \<username\> -P \<password\> -H \<BMC IP address or
  BMC host name\> fru print]{.kbd .ph .userinput}

  或

  [openbmctool -U \<username\> -P \<password\> -H \<BMC IP address or
  BMC host name\> fru list]{.kbd .ph .userinput}
  :::
- [若要顯示所有 FRU 項目的已知狀態，請使用下列指令：]{.cmd}

  :::: {.itemgroup .info}
  [openbmctool -U \<username\> -P \<password\> -H \<BMC IP address or
  BMC host name\> fru status]{.kbd .ph .userinput}

  ::: note
  [附註:]{.notetitle} BMC 必須將 FRU 項目指定為可更換的 FRU。
  :::
  ::::
- [如果要自動檢閱 FRU
  狀態指令，並判斷系統是否受到效能影響，請使用下列指令：]{.cmd}

  :::: {.itemgroup .info}
  [openbmctool -U \<username\> -P \<password\> -H \<BMC IP address or
  BMC host name\> health_check]{.kbd .ph .userinput}

  ::: note
  [附註:]{.notetitle}
  此指令不保證健全的系統，因為可能有與庫存項目無關的系統事件日誌項目。
  :::
  ::::
::::

## 系統 BMC 重設指令 {#task_o31_d12_sdb__title__1 .topictitle2}

:::: {.body .taskbody}
進一步瞭解系統 BMC 重設指令。

::: tasklabel
### 程序 {#tasktask_o31_d12_sdb__steps-unordered__1 .sectiontitle .tasklabel}
:::

- [若要從遠端進行 BMC 的暖重設，且沒有 AC 循環，請使用下列指令： ]{.cmd}

  ::: {.itemgroup .info}
  [openbmctool -U \<username\> -P \<password\> -H \<BMC IP address or
  BMC host name\> bmc reset warm]{.kbd .ph .userinput}
  :::
- [若要從遠端執行 BMC 冷重設，且沒有 AC 循環，請使用下列指令： ]{.cmd}

  ::: {.itemgroup .info}
  [openbmctool -U \<username\> -P \<password\> -H \<BMC IP address or
  BMC host name\> bmc reset cold]{.kbd .ph .userinput}
  :::
::::

## 系統傾出指令 {#task_alp_s12_sdb__title__1 .topictitle2}

:::: {.body .taskbody}
進一步瞭解系統傾出指令。

::: tasklabel
### 程序 {#tasktask_alp_s12_sdb__steps-unordered__1 .sectiontitle .tasklabel}
:::

- [若要建立新的傾出檔，請使用下列指令： ]{.cmd}

  ::: {.itemgroup .info}
  [openbmctool -U \<username\> -P \<password\> -H \<BMC IP address or
  BMC host name\> dump create]{.kbd .ph .userinput}
  :::
- [若要列出系統中的所有傾出檔，請使用下列指令： ]{.cmd}

  ::: {.itemgroup .info}
  [openbmctool -U \<username\> -P \<password\> -H \<BMC IP address or
  BMC host name\> dump list]{.kbd .ph .userinput}
  :::
- [若要從系統中刪除特定的傾出檔，請使用下列指令： ]{.cmd}

  ::: {.itemgroup .info}
  [openbmctool -U \<username\> -P \<password\> -H \<BMC IP address or
  BMC host name\> dump delete -n \<dump file entry\>]{.kbd .ph
  .userinput}
  :::
- [若要從系統中刪除所有傾出檔，請使用下列指令： ]{.cmd}

  ::: {.itemgroup .info}
  [openbmctool -U \<username\> -P \<password\> -H \<BMC IP address or
  BMC host name\> dump delete all]{.kbd .ph .userinput}
  :::
- [若要擷取特定的傾出檔，請使用下列指令： ]{.cmd}

  ::: {.itemgroup .info}
  [openbmctool -U \<username\> -P \<password\> -H \<BMC IP address or
  BMC host name\> dump retrieve -n \<dump file entry\>]{.kbd .ph
  .userinput}
  :::
- [若要擷取傾出檔並將它儲存至特定目錄，請使用下列指令： ]{.cmd}

  ::::: {.itemgroup .info}
  :::: p
  [openbmctool -U \<username\> -P \<password\> -H \<BMC IP address or
  BMC host name\> dump retrieve -s \<location to save dump file\> ]{.kbd
  .ph .userinput}

  ::: note
  [附註:]{.notetitle} 如果未指定位置，則檔案會儲存在暫存目錄中執行指令的
  OS 中。
  :::
  ::::
  :::::
::::

## 啟用及停用本端 BMC 使用者帳戶 {#enableusers__title__1 .topictitle2}

:::::::: {.body .taskbody}
進一步瞭解 [local_users]{.ph .uicontrol} 指令。

:::::: {.section .section .context role="region" aria-label="啟用及停用本端 BMC 使用者帳戶: 關於此作業"}
::: tasklabel
### 關於此作業 {#taskenableusers__context__1 .sectiontitle .tasklabel}
:::

:::: p
可以使用 [local_users]{.ph .uicontrol} 次指令來停用、查詢及重新啟用 BMC
上的本端使用者帳戶（例如 root）。

::: note
[附註:]{.notetitle} 停用本端使用者之後， LDAP 使用者需要可供與 BMC
進一步互動，包括使用 OpenBMC 工具來啟用本端使用者。
:::
::::
::::::

::: tasklabel
### 程序 {#taskenableusers__steps-unordered__1 .sectiontitle .tasklabel}
:::

- [若要檢視現行本端使用者帳戶狀態，請使用下列指令： ]{.cmd}

  ::: {.itemgroup .info}
  [openbmctool \<connection options\> local_users queryenabled]{.kbd .ph
  .userinput}
  :::
- [若要停用所有本端使用者帳戶，請使用下列指令： ]{.cmd}

  ::: {.itemgroup .info}
  [openbmctool \<connection options\> local_users disableall]{.kbd .ph
  .userinput}
  :::
- [[若要啟用所有本端使用者帳戶，請使用下列指令：
  ]{.cmd}]{#enableusers__step1}

  ::: {.itemgroup .info}
  [openbmctool \<connection options\> local_users enableall]{.kbd .ph
  .userinput}
  :::
::::::::

## 使用 rsyslog 進行遠端記載 {#task_f5k_xfh_1gb__title__1 .topictitle2}

:::::: {.body .taskbody}
進一步瞭解遠端記載指令。

:::: {.section .section .context role="region" aria-label="使用 rsyslog 進行遠端記載: 關於此作業"}
::: tasklabel
### 關於此作業 {#tasktask_f5k_xfh_1gb__context__1 .sectiontitle .tasklabel}
:::

BMC 可以使用
[RSYSLOG](https://www.rsyslog.com/ "（在新的標籤或視窗中開啟）"){rel="noopener"
target="_blank"} 來串流出本端日誌（移至 systemd 日誌登載）。 BMC
會傳送日誌中的所有內容。 必須在 rsyslog
伺服器上管理任何類型的過濾及適當儲存體。
::::

::: tasklabel
### 程序 {#tasktask_f5k_xfh_1gb__steps-unordered__1 .sectiontitle .tasklabel}
:::

- [若要配置 rsyslog 伺服器進行遠端記載，請使用下列指令： ]{.cmd}

  :::: {.itemgroup .info}
  [openbmctool \<connection options\> logging remote_logging_config -a
  \<IP address\> -p \<port\>]{.kbd .ph .userinput}

  ::: note
  [附註:]{.notetitle} IP 位址及埠適用於遠端 rsyslog 伺服器。
  執行指令之後，遠端 rsyslog 伺服器會開始從 BMC 接收日誌。
  :::
  ::::
- [若要停用遠端記載，請使用下列指令： ]{.cmd}

  :::: {.itemgroup .info}
  [openbmctool \<connection options\> logging remote_logging
  disable]{.kbd .ph .userinput}

  ::: note
  [附註:]{.notetitle}
  在將遠端記載從現有遠端伺服器切換至新伺服器之前，請先停用遠端記載。
  :::
  ::::
- [若要檢視遠端記載配置，請使用下列指令： ]{.cmd}

  :::: {.itemgroup .info}
  [openbmctool \<connection options\> logging remote_logging view]{.kbd
  .ph .userinput}

  ::: note
  [附註:]{.notetitle} 這個指令會以 JavaScript Object Notation (JSON)
  格式印出遠端 rsyslog 伺服器的 IP 位址和埠。
  :::
  ::::
- [若要開啟 REST API 記載，請使用下列指令： ]{.cmd}

  ::: {.itemgroup .info}
  [openbmctool \<connection options\> logging rest_api on]{.kbd .ph
  .userinput}
  :::
- [若要關閉 REST API 記載，請使用下列指令： ]{.cmd}

  :::: {.itemgroup .info}
  [openbmctool \<connection options\> logging rest_api off]{.kbd .ph
  .userinput}

  ::: note
  [附註:]{.notetitle} 依預設會關閉 REST API 記載。
  :::
  ::::
::::::

## 憑證管理 {#task_zjk_lhh_1gb__title__1 .topictitle2}

:::::: {.body .taskbody}
進一步瞭解憑證管理指令。

:::: {.section .section .context role="region" aria-label="憑證管理: 關於此作業"}
::: tasklabel
### 關於此作業 {#tasktask_zjk_lhh_1gb__context__1 .sectiontitle .tasklabel}
:::

可以將現有的憑證和私密金鑰檔取代為另一個（可能是 CA
簽署）憑證和私密金鑰檔。 可以安裝伺服器、用戶端及 root 憑證。
::::

::: tasklabel
### 程序 {#tasktask_zjk_lhh_1gb__steps-unordered__1 .sectiontitle .tasklabel}
:::

- [若要更新 HTTP 伺服器憑證，請使用下列指令： ]{.cmd}

  :::: {.itemgroup .info}
  [openbmctool \<connection options\> certificate update server https -f
  \<File\>]{.kbd .ph .userinput}

  ::: note
  [附註:]{.notetitle} [\<File\>]{.kbd .ph .userinput}
  是同時包含憑證及私密金鑰的隱私權加強型郵件 (PEM) 檔案。
  :::
  ::::
- [若要更新 LDAP 用戶端憑證，請使用下列指令： ]{.cmd}

  :::: {.itemgroup .info}
  [openbmctool \<connection options\> certificate update client ldap -f
  \<File\>]{.kbd .ph .userinput}

  ::: note
  [附註:]{.notetitle} [\<File\>]{.kbd .ph .userinput}
  是同時包含憑證和私密金鑰的 PEM 檔案。
  :::
  ::::
- [若要更新 LDAP 主要憑證，請使用下列指令： ]{.cmd}

  :::: {.itemgroup .info}
  [openbmctool \<connection options\> certificate update authority ldap
  -f \<File\>]{.kbd .ph .userinput}

  ::: note
  [附註:]{.notetitle} [\<File\>]{.kbd .ph .userinput} 是僅包含憑證的 PEM
  檔案。
  :::
  ::::
- [若要刪除 HTTP 伺服器憑證，請使用下列指令： ]{.cmd}

  :::: {.itemgroup .info}
  [openbmctool \<connection options\> certificate delete server
  https]{.kbd .ph .userinput}

  ::: note
  [附註:]{.notetitle} 刪除憑證會建立並安裝新的自簽憑證。
  :::
  ::::
- [若要刪除 LDAP 用戶端憑證，請使用下列指令： ]{.cmd}

  ::: {.itemgroup .info}
  [openbmctool \<connection options\> certificate delete client
  ldap]{.kbd .ph .userinput}
  :::
- [若要刪除 LDAP root 憑證，請使用下列指令： ]{.cmd}

  :::: {.itemgroup .info}
  [openbmctool \<connection options\> certificate delete authority
  ldap]{.kbd .ph .userinput}

  ::: note
  [附註:]{.notetitle} 刪除主要憑證可能會導致 LDAP 服務中斷。
  :::
  ::::
::::::

## LDAP 配置 {#ldap__title__1 .topictitle2}

:::::: {.body .taskbody}
進一步瞭解 LDAP 配置指令。

:::: {.section .section .context role="region" aria-label="LDAP 配置: 關於這項作業"}
::: tasklabel
### 關於此作業 {#taskldap__context__1 .sectiontitle .tasklabel}
:::

在 BMC 中，LDAP 用於遠端鑑別。 BMC 不支援遠端使用者管理功能。 BMC
同時支援安全及非安全 LDAP 配置。
::::

::: tasklabel
### 程序 {#taskldap__steps-unordered__1 .sectiontitle .tasklabel}
:::

- [若要建立 LDAP 配置（非安全），請使用下列指令： ]{.cmd}

  :::: {.itemgroup .info}
  [openbmctool.py \<connection options\> ldap enable
  \--uri=\"ldap://\<ldap server IP/hostname\>\" \--bindDN=\<bindDN\>
  \--baseDN=\<basDN\> \--bindPassword=\<bindPassword\>
  \--scope=\"sub/one/base\"
  \--serverType=\"OpenLDAP/ActiveDirectory\"]{.kbd .ph .userinput}

  ::: note
  [附註:]{.notetitle} 在 [uri]{.kbd .ph .userinput}
  參數中配置完整網域名稱或主機名稱需要在 BMC 上配置網域名稱系統 (DNS)
  伺服器。
  :::
  ::::
- [若要建立 LDAP 配置（安全），請使用下列指令： ]{.cmd}

  :::: {.itemgroup .info}
  [openbmctool.py \<connection options\> ldap enable
  \--uri=\"ldaps://\<ldap server IP/hostname\>\" \--bindDN=\<bindDN\>
  \--baseDN=\<basDN\> \--bindPassword=\<bindPassword\>
  \--scope=\"sub/one/base\"
  \--serverType=\"OpenLDAP/ActiveDirectory\"]{.kbd .ph .userinput}

  ::: {.note .note}
  [附註：]{.notetitle}
  1.  當執行上述 [openbmctool.py]{.kbd .ph .userinput}
      指令字串時，通常會遇到下列錯誤：

      [xyz.openbmc_project.Common.Error.NoCACertificate]{.ph .uicontrol}

      此錯誤表示 BMC 用戶端需要驗證 LDAP
      伺服器憑證是否由已知憑證管理中心 (CA) 簽署。 管理者需要將 CA
      憑證上傳至 BMC 才能解決此錯誤。

  2.  OpenBMC 工具不支援個別 LDAP 配置內容更新。
      若要更新個別內容，管理者必須使用已變更的值重建 LDAP 配置。
  :::
  ::::
- [若要刪除 LDAP 配置，請使用下列指令： ]{.cmd}

  :::: {.itemgroup .info}
  [openbmctool.py \<connection options\> ldap disable]{.kbd .ph
  .userinput}

  ::: note
  [附註:]{.notetitle} 在執行指令之前必須先啟用 root 使用者，否則無法存取
  BMC。 若要啟用所有本端使用者帳戶，請參閱
  [啟用及停用本端使用者帳戶](#enableusers__step1)。
  :::
  ::::
- [[若要新增專用權對映，請使用下列指令： ]{.cmd}]{#ldap__step2}

  ::: {.itemgroup .info}
  [openbmctool.py \<connection options\> ldap privilege-mapper create
  \--groupName=\<groupName\> \--privilege=\"priv-admin/priv-user\"]{.kbd
  .ph .userinput}
  :::
- [若要刪除專用權對映，請使用下列指令： ]{.cmd}

  ::: {.itemgroup .info}
  [openbmctool.py \<connection options\> ldap privilege-mapper delete
  \--groupName=\<groupName\>]{.kbd .ph .userinput}
  :::
- [若要列出專用權對映，請使用下列指令： ]{.cmd}

  ::: {.itemgroup .info}
  [openbmctool.py \<connection options\> ldap privilege-mapper
  list]{.kbd .ph .userinput}
  :::

  :::: {.itemgroup .info}
  ::: p
  LDAP 配置的一般工作流程順序如下：
  1.  配置 DNS 伺服器。
  2.  配置 LDAP。
      a.  配置 CA 憑證以進行安全 LDAP 配置。
      b.  使用本端使用者建立 LDAP 配置。
  3.  配置使用者專用權。
  :::
  ::::

  :::: {.itemgroup .info}
  ::: {.note .note}
  [附註：]{.notetitle}
  1.  如果使用 LDAP 認證登入，且尚未新增 LDAP
      認證的專用權對映，則會收到下列錯誤訊息：

      [403，「LDAP 群組專用權對映不存在」。]{.ph .uicontrol}

      可以透過新增[專用權對映](#ldap__step2)來避免此錯誤。

  2.  下列錯誤訊息可能表示使用者對 BMC 缺乏足夠的專用權：

      [專用權不足]{.ph .uicontrol}

      可以透過新增[專用權對映](#ldap__step2)來避免此錯誤。

  3.  在設定 LDAP 之後，OpenBMC 工具連線選項可同時與 LDAP
      及本端使用者搭配使用。
  :::
  ::::
::::::

## 網路配置 {#task_mtp_kgw_1gb__title__1 .topictitle2}

:::: {.body .taskbody}
進一步瞭解網路配置指令。

::: tasklabel
### 程序 {#tasktask_mtp_kgw_1gb__steps-unordered__1 .sectiontitle .tasklabel}
:::

- [若要啟用 DHCP，請使用下列指令： ]{.cmd}

  ::: {.itemgroup .info}
  [openbmctool.py -H \<BMC_IP\> -U root -P \<root password\> network
  enableDHCP -I \<Interface name\>]{.kbd .ph .userinput}
  :::
- [若要停用 DHCP，請使用下列指令： ]{.cmd}

  ::: {.itemgroup .info}
  [openbmctool.py -H \<BMC_IP\> -U root -P \<root password\> network
  disableDHCP -I \<Interface name\>]{.kbd .ph .userinput}
  :::
- [若要取得主機名稱，請使用下列指令： ]{.cmd}

  ::: {.itemgroup .info}
  [openbmctool.py -H \<BMC_IP\> -U root -P \<root password\> network
  getHostName]{.kbd .ph .userinput}
  :::
- [若要設定主機名稱，請使用下列指令： ]{.cmd}

  ::: {.itemgroup .info}
  [openbmctool.py -H \<BMC_IP\> -U root -P \<root password\> network
  setHostName -H \<host name\>]{.kbd .ph .userinput}
  :::
- [若要取得網域名稱，請使用下列指令： ]{.cmd}

  ::: {.itemgroup .info}
  [openbmctool.py -H \<BMC_IP\> -U root -P \<root password\> network
  getDomainName -I \<Interface name\>]{.kbd .ph .userinput}
  :::
- [若要設定網域名稱，請使用下列指令： ]{.cmd}

  ::: {.itemgroup .info}
  [openbmctool.py -H \<BMC_IP\> -U root -P \<root password\> network
  setDomainName -I \<Interface name\> -D
  DomainName1,DomainName2,..]{.kbd .ph .userinput}
  :::
- [若要取得媒體存取控制 (MAC) 位址，請使用下列指令： ]{.cmd}

  ::: {.itemgroup .info}
  [openbmctool.py -H \<BMC_IP\> -U root -P \<root password\> network
  getMACAddress -I \<Interface name\>]{.kbd .ph .userinput}
  :::
- [若要設定 MAC 位址，請使用下列指令： ]{.cmd}

  ::: {.itemgroup .info}
  [openbmctool.py -H \<BMC_IP\> -U root -P \<root password\> network
  setMACAddress -I \<Interface name\> -MA xx:xx:xx:xx:xx]{.kbd .ph
  .userinput}
  :::
- [若要取得預設閘道，請使用下列指令： ]{.cmd}

  ::: {.itemgroup .info}
  [openbmctool.py -H \<BMC_IP\> -U root -P \<root password\> network
  getDefaultGW]{.kbd .ph .userinput}
  :::
- [若要設定預設閘道，請使用下列指令： ]{.cmd}

  ::: {.itemgroup .info}
  [openbmctool.py -H \<BMC_IP\> -U root -P \<root password\> network
  setDefaultGW -GW \<default gw\>]{.kbd .ph .userinput}
  :::
- [若要檢視現行網路配置，請使用下列指令： ]{.cmd}

  ::: {.itemgroup .info}
  [openbmctool.py -H \<BMC_IP\> -U root -P \<root password\> network
  view-config]{.kbd .ph .userinput}
  :::
- [若要取得網路時間通訊協定 (NTP) ，請使用下列指令： ]{.cmd}

  ::: {.itemgroup .info}
  [openbmctool.py -H \<BMC_IP\> -U root -P \<root password\> network
  getNTP -I \<Interface name\>]{.kbd .ph .userinput}
  :::
- [若要設定 NTP，請使用下列指令： ]{.cmd}

  ::: {.itemgroup .info}
  [openbmctool.py -H \<BMC_IP\> -U root -P \<root password\> network
  setNTP -I \<Interface name\> -N NTP1,NTP2,\...]{.kbd .ph .userinput}
  :::
- [若要取得網域名稱系統 (DNS) ，請使用下列指令： ]{.cmd}

  ::: {.itemgroup .info}
  [openbmctool.py -H \<BMC_IP\> -U root -P \<root password\> network
  getDNS -I \<Interface name\>]{.kbd .ph .userinput}
  :::
- [若要設定 DNS，請使用下列指令： ]{.cmd}

  ::: {.itemgroup .info}
  [openbmctool.py -H \<BMC_IP\> -U root -P \<root password\> network
  setDNS -I \<Interface name\> -d DNS1,DNS2,\...]{.kbd .ph .userinput}
  :::
- [若要取得 IP 位址，請使用下列指令： ]{.cmd}

  ::: {.itemgroup .info}
  [openbmctool.py -H \<BMC_IP\> -U root -P \<root password\> network
  getIP -I \<Interface name\>]{.kbd .ph .userinput}
  :::
- [若要設定 IP 位址，請使用下列指令： ]{.cmd}

  ::: {.itemgroup .info}
  [openbmctool.py -H \<BMC_IP\> -U root -P \<root password\> network
  addIP -a \<ADDRESS\> \\]{.kbd .ph .userinput}[-gw \<GATEWAY\> -l
  \<PREFIXLENGTH\> -p \<protocol type\> -I \<Interface name\>]{.kbd .ph
  .userinput}
  :::
- [若要刪除 IP 位址，請使用下列指令： ]{.cmd}

  ::: {.itemgroup .info}
  [openbmctool.py -H \<BMC_IP\> -U root -P \<root password\> network
  rmIP -I \<Interface name\> -a \<ADDRESS\>]{.kbd .ph .userinput}
  :::
- [若要啟用虛擬區域網路 (VLAN)，請使用下列指令： ]{.cmd}

  ::: {.itemgroup .info}
  [openbmctool.py \<connection options\> network addVLAN -I \<Interface
  name\> -n \<IDENTIFIER\>]{.kbd .ph .userinput}
  :::
- [若要停用虛擬區域網路 (VLAN)，請使用下列指令： ]{.cmd}

  ::: {.itemgroup .info}
  [openbmctool.py \<connection options\> network deleteVLAN -I
  \<Interface name\>]{.kbd .ph .userinput}
  :::
- [若要檢視 DHCP 配置內容，請使用下列指令： ]{.cmd}

  ::: {.itemgroup .info}
  [openbmctool.py \<connection options\> network viewDHCPConfig]{.kbd
  .ph .userinput}
  :::
- [若要配置 DHCP 內容，請使用下列指令： ]{.cmd}

  :::: {.itemgroup .info}
  [openbmctool.py \<connection options\> network configureDHCP -d
  \<DNSENABLED\> -n \<HOSTNAMEENABLED\> -t \<NTPENABLED\> -s
  \<SENDHOSTNAMEENABLED\>]{.kbd .ph .userinput}

  ::: note
  [附註:]{.notetitle} [DNSENABLED]{.kbd .ph .userinput}、
  [HOSTNAMEENABLED]{.kbd .ph .userinput}、 [NTPENABLED]{.kbd .ph
  .userinput}和 [SENDHOSTNAMEENABLED]{.kbd .ph .userinput} 是布林值
  (true 或 false)。
  :::
  ::::
- [若要將網路設定重設為原廠預設值，請使用下列指令： ]{.cmd}

  :::: {.itemgroup .info}
  [openbmctool.py \<connection options\> network nwReset]{.kbd .ph
  .userinput}

  ::: note
  [附註:]{.notetitle} 在 BMC 重新開機之後套用重設設定。
  :::
  ::::
::::

:::: familylinks
::: parentlink
**上層主題:** [使用 OpenBMC
工具來管理系統](p10hai_openbmc_openbmctool.htm "瞭解如何使用 OpenBMC 工具來配置及管理系統。"){hd-product="POWER10"}
:::
::::
