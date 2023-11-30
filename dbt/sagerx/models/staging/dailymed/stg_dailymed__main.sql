 /* staging.stg_dailymed__main */

with xml_table as
(
	select spl, xml_content::xml as xml_column
	from datasource.dailymed
)

select spl, y.*, 'https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=' || y.set_id
    from   xml_table x,
            xmltable('dailymed'
              passing xml_column
              columns 
                document_id 	TEXT  PATH './documentId',
				set_id  		TEXT  PATH './SetId',
				version_number	TEXT  PATH './VersionNumber',
  				effective_date	TEXT  PATH './EffectiveDate',
				market_status	TEXT  PATH './MarketStatus',
				application_number TEXT PATH './ApplicationNumber'
					) y
